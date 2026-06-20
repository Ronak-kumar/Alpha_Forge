import os
import sys
from pathlib import Path

# Ensure local source path is importable when running the worker script directly.
source_dir = Path(__file__).resolve().parents[1]
root_dir = source_dir.parents[2]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(source_dir))

from .celery_app import celery_app
from apps.data_service.src.config.logger import get_logger

logger = get_logger("api.worker")
RABBIT_QUEUE = os.getenv("RABBITMQ_QUEUE", "data_monthly_jobs")


if __name__ == "__main__":
    logger.info("Starting Celery worker for queue=%s", RABBIT_QUEUE)
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--queues",
        RABBIT_QUEUE,
    ])
