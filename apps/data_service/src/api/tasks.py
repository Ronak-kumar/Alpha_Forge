from api.celery_app import celery_app
from api.monthly import create_monthly_data
from config.logger import get_logger

logger = get_logger("api.tasks")


@celery_app.task(bind=True, name="alpha_forge.create_monthly_data")
def create_monthly_data_task(self, segment: str, year: int, month: int, events: list, request_id: str = None):
    logger.info("Celery task start: %s", request_id)
    try:
        # call the async function from monthly.py synchronously by running an event loop
        import asyncio

        return asyncio.get_event_loop().run_until_complete(create_monthly_data(segment, year, month, events))
    except Exception as exc:
        logger.error("Celery task failed %s: %s", request_id, exc)
        raise
