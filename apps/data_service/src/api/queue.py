import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.data_service.src.config.logger import get_logger
from api.monthly import create_monthly_data, ensure_or_validate_manifest

logger = get_logger("api.queue")

QUEUE_DIR = Path(__file__).resolve().parents[1] / "queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

_job_queue: "asyncio.Queue[JobMessage]" = asyncio.Queue()


@dataclass
class JobMessage:
    segment: str
    year: int
    month: int
    events: Optional[List[Dict[str, Any]]]
    request_id: str


async def enqueue_job(job: JobMessage) -> None:
    await _job_queue.put(job)
    logger.info(f"Enqueued monthly job {job.request_id} for {job.segment}/{job.year}/{job.month}")


async def _process_job(job: JobMessage) -> Dict[str, Any]:
    logger.info(f"Processing job {job.request_id}")
    result = await ensure_or_validate_manifest(job.segment, job.year, job.month, job.events)
    logger.info(f"Finished job {job.request_id} with status {result['status']}")
    return result


async def worker_loop() -> None:
    while True:
        job = await _job_queue.get()
        try:
            await _process_job(job)
        except Exception as exc:
            logger.error(f"Job {job.request_id} failed: {exc}")
        finally:
            _job_queue.task_done()


def get_queue_size() -> int:
    return _job_queue.qsize()
