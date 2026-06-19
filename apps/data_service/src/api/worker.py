import asyncio
import json
import os
from typing import Any, Dict

import aio_pika

from monthly import create_monthly_data
from apps.data_service.src.config.logger import get_logger

logger = get_logger("api.worker")

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
RABBIT_QUEUE = os.getenv("RABBITMQ_QUEUE", "data_monthly_jobs")


async def _handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            segment = payload.get("segment")
            year = int(payload.get("year"))
            month = int(payload.get("month"))
            events = payload.get("events")
            request_id = payload.get("request_id")

            logger.info("Worker picked job %s for %s/%s/%s", request_id, segment, year, month)
            await create_monthly_data(segment, year, month, events)
            logger.info("Worker finished job %s", request_id)
        except Exception as exc:
            logger.error("Failed to process message: %s", exc)


async def run_worker():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(RABBIT_QUEUE, durable=True)

    await queue.consume(_handle_message, no_ack=False)

    logger.info("Started RabbitMQ worker listening on %s", RABBIT_QUEUE)

    # Keep the worker running
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await channel.close()
        await connection.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
