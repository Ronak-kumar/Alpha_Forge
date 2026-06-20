from celery import Celery
from kombu import Queue
import os

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost//")
RABBIT_QUEUE = os.getenv("RABBITMQ_QUEUE", "data_monthly_jobs")

celery_app = Celery(
    "alpha_forge",
    broker=RABBIT_URL,
    backend=None,
    include=["tasks.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    task_default_queue=RABBIT_QUEUE,
    task_queues=(Queue(RABBIT_QUEUE, routing_key=RABBIT_QUEUE),),
    task_default_exchange=RABBIT_QUEUE,
    task_default_exchange_type="direct",
    task_default_routing_key=RABBIT_QUEUE,
)
