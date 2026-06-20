import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import HTTPException

from apps.data_service.src.config.logger import get_logger
from apps.data_service.src.helpers.utill import _ensure_path, _manifest_path, _month_path


logger = get_logger("api.monthly")


def _build_manifest(files: List[Dict[str, Any]], symbols: List[str]) -> Dict[str, Any]:
    if not files:
        raise ValueError("Cannot build manifest without file metadata")

    min_ts = min(f["min_ts"] for f in files)
    max_ts = max(f["max_ts"] for f in files)
    row_count = sum(f.get("row_count", 0) for f in files)
    return {
        "segment": files[0]["segment"],
        "year": files[0]["year"],
        "month": files[0]["month"],
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
    return {
        "name": path.name,
        "segment": events[0]["segment"],
        "year": events[0]["year"],
        "month": events[0]["month"],
        "symbol": events[0]["symbol"],
        "min_ts": min(timestamps),
        "max_ts": max(timestamps),
        "row_count": len(events),
    }


async def create_monthly_data(segment: str, year: int, month: int, symbol: str, exchange: str) -> Dict[str, Any]:
    if segment == "FNO":
        folder_path = ["INDEX", "OPTION"]
    elif segment == "EQUITY":
        folder_path = ["EQUITY"]
    elif segment == "CRYPTO":
        folder_path = ["CRYPTO"]

    for folder in folder_path:
        month_path = _month_path(folder, symbol)
        _ensure_path(month_path)

        file_path = month_path / f"{symbol}_{year}_{month:02d}.parquet"
        file_meta = _write_parquet_file(file_path)
        manifest = _build_manifest([file_meta], [file_meta["symbol"]])
        manifest_path = _manifest_path(folder, symbol)
        manifest_path.write_text(json.dumps(manifest, indent=2))

        logger.info(f"Created monthly parquet and manifest: {file_path}")
    return {
        "path": str(file_path),
        "manifest": manifest,
    }


async def ensure_or_validate_manifest(segment: str, year: int, month: int, events: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    manifest_path = _manifest_path(segment, year, month)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if events is not None:
            _validate_manifest(manifest, events)
        return {"manifest": manifest, "status": "validated"}

    if events is None:
        raise HTTPException(status_code=400, detail="No events provided to create missing monthly metadata")

    result = await create_monthly_data(segment, year, month, symbol, exchange, events)
    return {"manifest": result["manifest"], "status": "created"}


def get_monthly_manifest(segment: str, year: int, month: int) -> Dict[str, Any]:
    manifest_path = _manifest_path(segment, year, month)
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Monthly manifest not found")
    return json.loads(manifest_path.read_text())


def get_monthly_data(segment: str, year: int, month: int) -> Dict[str, Any]:
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
