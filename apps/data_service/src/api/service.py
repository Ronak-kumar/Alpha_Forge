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
from apps.data_service.src.helpers.utill import _month_path, _manifest_path, _ensure_path

logger = get_logger("api.service")
DATA_BASE = Path(__file__).resolve().parents[1] / "cache"
MANIFEST_NAME = "manifest.json"


router = APIRouter(prefix="/data", tags=["data"])


@router.post("/Indices/month",
    description=f"""
    {model_docs(MonthlyDataRequest)}
    """)
def create_or_validate_monthly_data(request: MonthlyDataRequest, fastapi_request: Request):
    # Extract parameters from the request
    segment = request.segment
    year = request.year
    month = request.month
    symbol = request.symbol
    exchange = request.exchange

    # path for the month and manifest
    month_path = _month_path(segment, symbol)
    _ensure_path(month_path)
    manifest_path = _manifest_path(segment, symbol)

    # If the manifest already exists, return it as validated
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        return {
            "segment": segment,
            "year": year,
            "month": month,
            "symbol": symbol,
            "exchange": exchange,
            "status": "validated",
            "manifest": manifest,
        }
    
    # If the manifest does not exist, enqueue a Celery task to create it
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())
    job = {
        "segment": segment,
        "year": year,
        "month": month,
        "symbol": symbol,
        "exchange": exchange,
        "request_id": request_id,
    }

    # Enqueue the Celery task to create monthly data
    try:
        # create_monthly_data_task.delay(
        #     args=[segment, year, month, symbol, exchange],
        #     kwargs={"request_id": request_id},
        # )
        create_monthly_data_task.apply_async(
            args=[segment, year, month, symbol, exchange],
            kwargs={"request_id": request_id},
        )
    except Exception as exc:
        logger.error("Failed to enqueue Celery task: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")

    return {
        "segment": segment,
        "year": year,
        "month": month,
        "status": "queued",
        "request_id": request_id,
    }

def _build_manifest(files: List[Dict[str, Any]], symbols: List[str]) -> Dict[str, Any]:
    min_ts = min(f["min_ts"] for f in files)
    max_ts = max(f["max_ts"] for f in files)
    row_count = sum(f.get("row_count", 0) for f in files)
    return {
        "segment": files[0]["segment"] if files else None,
        "year": files[0]["year"] if files else None,
        "month": files[0]["month"] if files else None,
        "symbols": sorted(set(symbols)),
        "files": files,
        "min_ts": min_ts,
        "max_ts": max_ts,
        "row_count": row_count,
    }


def _validate_manifest(manifest: Dict[str, Any], events: List[Dict[str, Any]]) -> None:
    symbols = sorted({event["symbol"] for event in events})
    if sorted(manifest.get("symbols", [])) != symbols:
        raise ValueError("Manifest symbol list does not match provided events")
    if manifest.get("row_count") is not None and manifest["row_count"] != len(events):
        raise ValueError("Manifest row count does not match provided events")


def _write_parquet_file(path: Path, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    _ensure_path(path.parent)
    table = pa.Table.from_pylist(events)
    pq.write_table(table, path)

    timestamps = [event["timestamp"] for event in events]
    symbol = events[0]["symbol"] if events else None
    return {
        "name": path.name,
        "segment": events[0]["segment"],
        "year": events[0]["year"],
        "month": events[0]["month"],
        "symbol": symbol,
        "min_ts": min(timestamps),
        "max_ts": max(timestamps),
        "row_count": len(events),
    }


def _create_monthly_data(segment: str, year: int, month: int, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    month_path = _month_path(segment, year, month)
    _ensure_path(month_path)

    file_path = month_path / f"{segment}_{year}_{month:02d}.parquet"
    file_meta = _write_parquet_file(file_path, events)
    manifest = _build_manifest([file_meta], [file_meta["symbol"]])
    manifest_path = _manifest_path(segment, year, month)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    logger.info(f"Created monthly parquet and manifest: {file_path}")
    return {
        "path": str(file_path),
        "manifest": manifest,
    }


def _ensure_or_validate_manifest(segment: str, year: int, month: int, events: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    manifest_path = _manifest_path(segment, year, month)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if events is not None:
            _validate_manifest(manifest, events)
        return {"manifest": manifest, "status": "validated"}

    if events is None:
        raise HTTPException(status_code=400, detail="No events provided to create missing monthly metadata")

    result = _create_monthly_data(segment, year, month, events)
    return {"manifest": result["manifest"], "status": "created"}


@router.post(
    "/month",
    description=f"""
    {model_docs(MonthlyDataRequest)}
    """
)
def create_or_validate_monthly_data(request: MonthlyDataRequest, fastapi_request: Request):
    segment = request.segment
    year = request.year
    month = request.month
    symbol = request.symbol
    exchange = request.exchange


    month_path = _month_path(segment, symbol)
    _ensure_path(month_path)
    manifest_path = _manifest_path(segment, symbol)

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        return {
            "segment": segment,
            "year": year,
            "month": month,
            "symbol": symbol,
            "exchange": exchange,
            "status": "validated",
            "manifest": manifest,
        }

    request_id = str(uuid.uuid4())
    job = {
        "segment": segment,
        "year": year,
        "month": month,
        "symbol": symbol,
        "exchange": exchange,
        "request_id": request_id,
    }

    try:
        # create_monthly_data_task.delay(
        #     args=[segment, year, month, symbol, exchange],
        #     kwargs={"request_id": request_id},
        # )
        create_monthly_data_task.apply_async(
            args=[segment, year, month, symbol, exchange],
            kwargs={"request_id": request_id},
        )
    except Exception as exc:
        logger.error("Failed to enqueue Celery task: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")

    return {
        "segment": segment,
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


@router.get(
    "/month/{segment}/{year}/{month}",
    summary="Retrieve monthly manifest metadata",
    description=(
        "Get the metadata manifest for a specific month's data.\n\n"
        "The manifest contains:\n"
        "- List of parquet files generated for this month.\n"
        "- Symbols (e.g., ticker symbols) included in the data.\n"
        "- Min and max timestamps for the month.\n"
        "- Total row count across all files.\n\n"
        "**Parameters:**\n"
        "- `segment`: Asset class (e.g., 'equity', 'crypto').\n"
        "- `year`: Year (2000-2100).\n"
        "- `month`: Month (1-12).\n"
    )
)
def get_monthly_manifest(segment: str, year: int, month: int):
    manifest_path = _manifest_path(segment, year, month)
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Monthly manifest not found")
    return json.loads(manifest_path.read_text())


@router.get(
    "/month/{segment}/{year}/{month}/data",
    summary="Retrieve monthly data records",
    description=(
        "Fetch all data records (rows) for a specific month. Returns data from all parquet files for that month.\n\n"
        "**Parameters:**\n"
        "- `segment`: Asset class (e.g., 'equity', 'crypto').\n"
        "- `year`: Year (2000-2100).\n"
        "- `month`: Month (1-12).\n\n"
        "**Returns:**\n"
        "- `rows`: Array of all data records for the month.\n"
        "- `count`: Total number of records returned.\n\n"
        "**Warning:** This endpoint may return large payloads if many records exist for a month. Use responsibly.\n"
    )
)
def get_monthly_data(segment: str, year: int, month: int):
    month_path = _month_path(segment, year, month)
    if not month_path.exists():
        raise HTTPException(status_code=404, detail="Monthly month path not found")

    parquet_files = sorted(month_path.glob("*.parquet"))
    if not parquet_files:
        raise HTTPException(status_code=404, detail="No parquet files found for requested month")

    rows = []
    for parquet_file in parquet_files:
        table = pq.read_table(str(parquet_file))
        rows.extend(table.to_pylist())

    return {
        "segment": segment,
        "year": year,
        "month": month,
        "rows": rows,
        "count": len(rows),
    }
