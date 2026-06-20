from .celery_app import celery_app, RABBIT_QUEUE
from services.monthly import create_monthly_data
from apps.data_service.src.config.logger import get_logger
import asyncio


logger = get_logger("tasks")


@celery_app.task(bind=True, name="alpha_forge.create_monthly_data", queue=RABBIT_QUEUE)
def create_monthly_data_task(self, segment: str, year: int, month: int, symbol: str, exchange: str, request_id: str = None):
    logger.info("Celery task start: %s", request_id)
    try:
        return asyncio.run(create_monthly_data(segment, year, month, symbol, exchange))
    except Exception as exc:
        logger.error("Celery task failed %s: %s", request_id, exc, exc_info=True)
        raise
