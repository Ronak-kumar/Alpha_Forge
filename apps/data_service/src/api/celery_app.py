from celery import Celery
import os

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost//")

celery_app = Celery(
    "alpha_forge",
    broker=RABBIT_URL,
    backend=None,
)

# Optional: configure Celery with recommended settings for reliability
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
)
