import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict, Optional
from datetime import datetime

from app.db.models.analytics_data import AnalyticsData
from app.schemas.events import TaskCreatedPayload, TaskStatusChangedPayload

logger = logging.getLogger(__name__)

async def handle_task_creation(db: AsyncSession, payload: TaskCreatedPayload) -> None:
    """Handles the 'task_created' event."""
    logger.info(f"Processing task_created event for task_id: {payload.task_id}")
    try:
        # Create an entry in AnalyticsData to mark task creation
        analytics_entry = AnalyticsData(
            metric_key="task_lifecycle",
            metric_value={"status": "created", "title": payload.title, "priority": payload.priority},
            timestamp=payload.created_at, # Use timestamp from the event
            task_id=payload.task_id,
            company_id=payload.company_id,
            department_id=payload.department_id,
            user_id=payload.assignee_user_id # Initially assigned user
        )
        db.add(analytics_entry)
        await db.commit()
        logger.info(f"Saved 'created' status for task_id: {payload.task_id}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error handling task_created event for task {payload.task_id}: {e}", exc_info=True)

async def handle_task_status_change(db: AsyncSession, payload: TaskStatusChangedPayload) -> None:
    """Handles the 'task_status_changed' event."""
    logger.info(f"Processing task_status_changed event for task_id: {payload.task_id}")
    try:
        # Create an entry in AnalyticsData to record the status change
        analytics_entry = AnalyticsData(
            metric_key="task_lifecycle",
            metric_value={"status": payload.new_status, "previous_status": payload.old_status},
            timestamp=payload.changed_at, # Use timestamp from the event
            task_id=payload.task_id,
            company_id=payload.company_id,
            department_id=payload.department_id,
            user_id=payload.assignee_user_id # Current assignee
            # Consider adding changed_by_user_id if available/needed
        )
        db.add(analytics_entry)
        await db.commit()
        logger.info(f"Saved '{payload.new_status}' status for task_id: {payload.task_id}")

    except Exception as e:
        await db.rollback()
        logger.error(f"Error handling task_status_changed event for task {payload.task_id}: {e}", exc_info=True)

# Add handlers for other events (priority changed, assignee changed, etc.) as needed
# async def handle_task_priority_change(...)
# async def handle_task_assignee_change(...)

# --- Analytics Query Functions ---

async def get_task_counts_by_status(db: AsyncSession, company_id: Optional[int] = None) -> Dict[str, int]:
    """Calculates the count of tasks for each current status.
    
    This query finds the latest 'task_lifecycle' event for each task_id 
    and counts tasks based on the status in that latest event.
    NOTE: This can be inefficient on large datasets. Consider a snapshot table.
    """
    logger.info(f"Calculating task counts by status for company_id: {company_id}")

    # Subquery to find the latest timestamp for each task_id with metric_key='task_lifecycle'
    latest_event_subq = (
        select(
            AnalyticsData.task_id,
            func.max(AnalyticsData.timestamp).label("max_timestamp")
        )
        .where(AnalyticsData.metric_key == "task_lifecycle")
        .group_by(AnalyticsData.task_id)
        .alias("latest_event")
    )

    # Main query to join AnalyticsData with the subquery to get the latest event details
    query = (
        select(
            # Use ->> to extract JSON text field. Adjust based on your JSON structure
            # Ensure metric_value has a 'status' key
            AnalyticsData.metric_value.op('->>')(literal_column("'status'")).label("current_status"),
            func.count(distinct(AnalyticsData.task_id)).label("status_count")
        )
        .join(
            latest_event_subq,
            (AnalyticsData.task_id == latest_event_subq.c.task_id) &
            (AnalyticsData.timestamp == latest_event_subq.c.max_timestamp)
        )
        .where(AnalyticsData.metric_key == "task_lifecycle")
    )

    # Apply company filter if provided
    if company_id is not None:
        query = query.where(AnalyticsData.company_id == company_id)

    # Group by the extracted status
    query = query.group_by(literal_column("current_status"))

    try:
        result = await db.execute(query)
        status_counts = {row.current_status: row.status_count for row in result.all()}
        logger.info(f"Task counts by status calculated: {status_counts}")
        # Filter out null statuses if they appear (e.g., from events before status was added)
        return {k: v for k, v in status_counts.items() if k is not None}
    except Exception as e:
        logger.error(f"Error calculating task counts by status: {e}", exc_info=True)
        return {} 