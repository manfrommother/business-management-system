import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base_model import Base


class Report(Base):
    __tablename__ = "reports"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)  # e.g., "Monthly Task Performance"
    type = sa.Column(sa.String, index=True)  # e.g., "task_summary", "user_performance"
    # Parameters used to generate the report (filters, date ranges, etc.)
    parameters = sa.Column(JSONB, nullable=True)

    # Status of report generation (if generated asynchronously)
    status = sa.Column(sa.String, default="pending", index=True)  # e.g., pending, processing, completed, failed
    result_url = sa.Column(sa.String, nullable=True)  # Link to generated report file (e.g., S3 URL)
    error_message = sa.Column(sa.Text, nullable=True)

    # Who requested the report?
    requested_by_user_id = sa.Column(sa.Integer, index=True, nullable=False)
    company_id = sa.Column(sa.Integer, index=True, nullable=True)

    requested_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
    completed_at = sa.Column(sa.DateTime(timezone=True), nullable=True) 