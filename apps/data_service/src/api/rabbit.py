import json
import os
from typing import Any, Dict

import aio_pika
from aio_pika import Message, DeliveryMode

from apps.data_service.src.config.logger import get_logger

logger = get_logger("api.rabbit")

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
RABBIT_QUEUE = os.getenv("RABBITMQ_QUEUE", "data_monthly_jobs")


class RabbitPublisher:
    def __init__(self):
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None

    async def connect(self, url: str = None):
        url = url or RABBIT_URL
        self.connection = await aio_pika.connect_robust(url)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(RABBIT_QUEUE, durable=True)
        logger.info("RabbitMQ connected and queue declared: %s", RABBIT_QUEUE)

    async def publish(self, payload: Dict[str, Any], routing_key: str | None = None) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized")
        body = json.dumps(payload, default=str).encode()
        message = Message(body, delivery_mode=DeliveryMode.PERSISTENT)
        await self.channel.default_exchange.publish(message, routing_key=routing_key or RABBIT_QUEUE)
        logger.info("Published job to RabbitMQ queue=%s", routing_key or RABBIT_QUEUE)

    async def close(self) -> None:
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()


publisher = RabbitPublisher()
