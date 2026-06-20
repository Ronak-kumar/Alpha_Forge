import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import APIRouter, HTTPException, Request

from tasks import create_monthly_data_task
from apps.data_service.src.config.logger import get_logger
from .schemas import MonthlyDataRequest, model_docs
from apps.data_service.src.helpers.utill import _month_path, _manifest_path, _ensure_path, _build_manifest, _validate_manifest, _write_parquet_file

logger = get_logger("api.service")
DATA_BASE = Path(__file__).resolve().parents[1] / "cache"
MANIFEST_NAME = "manifest.json"


router = APIRouter(prefix="/data", tags=["data"])


@router.post("/month",
    description=f"""
    {model_docs(MonthlyDataRequest)}
    """)
def create_or_validate_monthly_data(request: MonthlyDataRequest, fastapi_request: Request):
    # Extract parameters from the request
    asset_class = request.asset_class
    year = request.year
    month = request.month
    symbol = request.symbol
    exchange = request.exchange
    
    # If the manifest does not exist, enqueue a Celery task to create it
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())

    # Enqueue the Celery task to create monthly data
    try:
        # create_monthly_data_task.delay(
        #     args=[segment, year, month, symbol, exchange],
        #     kwargs={"request_id": request_id},
        # )
        create_monthly_data_task.apply_async(
            args=[asset_class, year, month, symbol, exchange],
            kwargs={"request_id": request_id},
        )
    except Exception as exc:
        logger.error("Failed to enqueue Celery task: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")

    return {
        "asset_class": asset_class,
        "year": year,
        "month": month,
        "status": "queued",
        "request_id": request_id,
    }

@router.get(
    "/queue/status",
    summary="Get message queue status",
    description=(
        "Check the status of the RabbitMQ message queue. Returns a simple health status.\n\n"
        "**Notes:**\n"
        "- To view detailed queue metrics (message count, pending tasks), use the RabbitMQ Management UI at `http://localhost:15672`.\n"
        "- Credentials: user=`guest`, password=`guest`.\n"
    )
)
def queue_status():
    # When using RabbitMQ, return broker queue length is not trivial without management plugin.
    return {"status": "ok", "note": "Use RabbitMQ management UI to inspect queue length"}

