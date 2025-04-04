import asyncio
import logging
import json
from aio_pika import IncomingMessage
from pydantic import ValidationError

from app.core.messaging import consume_messages, connect_to_rabbitmq
from app.services import analytics_service # Import the analytics service
from app.db.session import AsyncSessionLocal
from app.schemas.events import TaskCreatedPayload, TaskStatusChangedPayload, Event

logger = logging.getLogger(__name__)

# Define queue names based on the services sending events
TASK_EVENTS_QUEUE = "task_events_analytics" # Example queue name
USER_EVENTS_QUEUE = "user_events_analytics" # Example queue name
COMPANY_EVENTS_QUEUE = "company_events_analytics" # Example queue name
CALENDAR_EVENTS_QUEUE = "calendar_events_analytics" # Example queue name

async def process_task_event(message: IncomingMessage) -> None:
    """Callback function to process messages from the task service queue."""
    async with message.process(ignore_processed=True): # Ensure message is ack/nack
        raw_body = message.body
        try:
            event_dict = json.loads(raw_body.decode())
            # Basic validation of event structure
            # validated_event = Event(**event_dict) # Might be too generic
            event_type = event_dict.get("event_type")
            payload_dict = event_dict.get("payload")

            if not event_type or not payload_dict:
                logger.error(f"Invalid event structure received: {event_dict}")
                # Nack the message? Or just log and ack?
                return

            logger.info(f"Received task event: {event_type}")
            logger.debug(f"Payload: {payload_dict}")

            # --- Processing Logic --- 
            async with AsyncSessionLocal() as db:
                try:
                    if event_type == "task_created":
                        validated_payload = TaskCreatedPayload(**payload_dict)
                        await analytics_service.handle_task_creation(db, validated_payload)
                    elif event_type == "task_status_changed":
                        validated_payload = TaskStatusChangedPayload(**payload_dict)
                        await analytics_service.handle_task_status_change(db, validated_payload)
                    # ... handle other task event types
                    else:
                        logger.warning(f"Unhandled task event type: {event_type}")
                        # Acknowledge the message even if unhandled for now

                    logger.debug(f"Event {event_type} processed successfully.")
                
                except ValidationError as e:
                    logger.error(f"Payload validation failed for event {event_type}: {e}")
                    logger.debug(f"Invalid payload: {payload_dict}")
                    # Decide how to handle validation errors (e.g., log, move to DLQ)
                    # Message will be acknowledged by context manager unless specific action taken
                
                except Exception as e:
                    # Specific database or service errors during handling
                    logger.error(f"Error handling event {event_type} in service: {e}", exc_info=True)
                    # Consider nack-ing the message for retry if appropriate
                    # await message.nack(requeue=True) # Example: Requeue for retry
                    # For now, let the context manager ack it after logging

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from message body: {raw_body}")
            # Message will be acknowledged by context manager
        except Exception as e:
            # Catch-all for unexpected errors during initial processing
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            # Message will be acknowledged by context manager

# Similarly, define processing functions for other event types (user, company, calendar)
# async def process_user_event(message: IncomingMessage) -> None: ...
# async def process_company_event(message: IncomingMessage) -> None: ...
# async def process_calendar_event(message: IncomingMessage) -> None: ...

async def start_consumers() -> None:
    """Connects to RabbitMQ and starts all defined consumers."""
    try:
        await connect_to_rabbitmq()
        # Start consumer for task events
        await consume_messages(TASK_EVENTS_QUEUE, process_task_event)
        logger.info(f"Consumer started for queue {TASK_EVENTS_QUEUE}")
        
        # Start consumers for other queues (uncomment when ready)
        # await consume_messages(USER_EVENTS_QUEUE, process_user_event)
        # logger.info(f"Consumer started for queue {USER_EVENTS_QUEUE}")
        # await consume_messages(COMPANY_EVENTS_QUEUE, process_company_event)
        # logger.info(f"Consumer started for queue {COMPANY_EVENTS_QUEUE}")
        # await consume_messages(CALENDAR_EVENTS_QUEUE, process_calendar_event)
        # logger.info(f"Consumer started for queue {CALENDAR_EVENTS_QUEUE}")

        logger.info("All event consumers started. Waiting for messages...")
        await asyncio.Event().wait() # Keeps the coroutine running indefinitely

    except ConnectionError as e:
        logger.error(f"Could not start consumers due to connection error: {e}")
    except Exception as e:
        logger.error(f"An error occurred while running consumers: {e}", exc_info=True)

# Entry point if running this consumer as a separate script/process
if __name__ == "__main__":
    # Make sure logging is configured correctly, especially if running standalone
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Starting event consumer script...")
    asyncio.run(start_consumers()) 