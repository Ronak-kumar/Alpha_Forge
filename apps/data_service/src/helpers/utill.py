
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import pyarrow as pa
import pyarrow.parquet as pq

DATA_BASE = Path(__file__).resolve().parents[1] / "cache"
MANIFEST_NAME = "manifest.json"


def _month_path(segment: str, symbol: str) -> Path:
    return DATA_BASE / segment / symbol


def _manifest_path(segment: str, symbol: str) -> Path:
    return _month_path(segment, symbol) / MANIFEST_NAME


def _ensure_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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