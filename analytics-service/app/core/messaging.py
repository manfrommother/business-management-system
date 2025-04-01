import asyncio
import logging
import aio_pika
from typing import Callable, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

connection: Optional[aio_pika.RobustConnection] = None
channel: Optional[aio_pika.Channel] = None

async def connect_to_rabbitmq() -> None:
    """Establishes a robust connection and channel to RabbitMQ."""
    global connection, channel
    if connection and not connection.is_closed:
        logger.info("RabbitMQ connection already established.")
        return

    loop = asyncio.get_running_loop()
    try:
        logger.info(f"Connecting to RabbitMQ at {settings.AMQP_URL}...")
        connection = await aio_pika.connect_robust(
            str(settings.AMQP_URL),
            loop=loop,
            timeout=10 # Add a connection timeout
        )
        channel = await connection.channel() # type: ignore
        await channel.set_qos(prefetch_count=10) # Process 10 messages at a time
        logger.info("Successfully connected to RabbitMQ and channel opened.")

        connection.add_close_callback(lambda sender, exc: logger.warning("RabbitMQ connection closed."))
        connection.add_reconnect_callback(lambda sender, conn: logger.info("Reconnected to RabbitMQ."))

    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
        # Implement retry logic or handle failure appropriately
        raise

async def close_rabbitmq_connection() -> None:
    """Closes the RabbitMQ connection and channel gracefully."""
    global connection, channel
    try:
        if channel and not channel.is_closed:
            await channel.close()
            logger.info("RabbitMQ channel closed.")
            channel = None
        if connection and not connection.is_closed:
            await connection.close()
            logger.info("RabbitMQ connection closed.")
            connection = None
    except Exception as e:
        logger.error(f"Error closing RabbitMQ connection: {e}", exc_info=True)

async def declare_queue(queue_name: str, durable: bool = True) -> aio_pika.Queue:
    """Declares a queue if it doesn't exist."""
    if not channel:
        await connect_to_rabbitmq()
        if not channel:
             raise ConnectionError("Failed to establish RabbitMQ channel for queue declaration.")
             
    logger.info(f"Declaring queue: {queue_name}")
    queue = await channel.declare_queue(queue_name, durable=durable)
    return queue

async def consume_messages(queue_name: str, callback: Callable[[aio_pika.IncomingMessage], None]) -> None:
    """Starts consuming messages from a specified queue."""
    if not channel:
        await connect_to_rabbitmq()
        if not channel:
             raise ConnectionError("Failed to establish RabbitMQ channel for consuming messages.")

    queue = await declare_queue(queue_name)
    logger.info(f"Starting consumer for queue: {queue_name}")
    await queue.consume(callback)
    logger.info(f"Consumer started for queue: {queue_name}") 