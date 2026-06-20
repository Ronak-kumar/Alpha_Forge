import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from tasks import create_monthly_data_task
from apps.data_service.src.config.logger import get_logger

logger = get_logger("api.service")
DATA_BASE = Path(__file__).resolve().parents[1] / "cache"
MANIFEST_NAME = "manifest.json"


class MonthlyDataRequest(BaseModel):
    segment: str = Field(..., description="Data segment name, e.g. equity")
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    events: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional list of events to create or validate monthly parquet data"
    )


router = APIRouter(prefix="/data", tags=["data"])


def _month_path(segment: str, year: int, month: int) -> Path:
    return DATA_BASE / segment / f"year={year}" / f"month={month:02d}"


def _manifest_path(segment: str, year: int, month: int) -> Path:
    return _month_path(segment, year, month) / MANIFEST_NAME


def _ensure_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


@router.post("/month")
def create_or_validate_monthly_data(request: MonthlyDataRequest, fastapi_request: Request):
    segment = request.segment
    year = request.year
    month = request.month
    events = request.events

    month_path = _month_path(segment, year, month)
    _ensure_path(month_path)
    manifest_path = _manifest_path(segment, year, month)

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if events:
            try:
                _validate_manifest(manifest, events)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
        return {
            "segment": segment,
            "year": year,
            "month": month,
            "status": "validated",
            "manifest": manifest,
        }

    if not events:
        raise HTTPException(status_code=400, detail="No events provided to create monthly data")

    request_id = str(uuid.uuid4())
    job = {
        "segment": segment,
        "year": year,
        "month": month,
        "events": events,
        "request_id": request_id,
    }

    try:
        create_monthly_data_task.apply_async(
            args=[segment, year, month, events],
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


@router.get("/queue/status")
def queue_status():
    # When using RabbitMQ, return broker queue length is not trivial without management plugin.
    return {"status": "ok", "note": "Use RabbitMQ management UI to inspect queue length"}


@router.get("/month/{segment}/{year}/{month}")
def get_monthly_manifest(segment: str, year: int, month: int):
    manifest_path = _manifest_path(segment, year, month)
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Monthly manifest not found")
    return json.loads(manifest_path.read_text())


@router.get("/month/{segment}/{year}/{month}/data")
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
