import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import pyarrow as pa
import pyarrow.parquet as pq
import os
from datetime import datetime

DATA_BASE = Path(__file__).resolve().parents[1] / "cache"


def _month_path(segment: str, symbol: str) -> Path:
    return DATA_BASE / segment / symbol


def _metadata_path(segment: str, symbol: str, year: int, month: int) -> Path:
    return _month_path(segment, symbol) / f"{symbol}_{year}_{month:02d}.json"


def _ensure_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_parquet_file(path: Path, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    _ensure_path(path.parent)
    table = pa.Table.from_pylist(events)
    pq.write_table(table, path)

    if events:
        return {
            "name": path.name,
            "symbol": events[0]["Symbol"],
            "row_count": len(events),
            "column_count": len(events[0]) if events else 0,
            "meta_file_last_update": datetime.now().isoformat(),
        }
    else:
        # Handle empty events case
        return {
            "name": None,
            "symbol": None,
            "row_count": 0,
            "column_count": 0,
            "meta_file_last_update": ""
            }


def _get_db_and_table(asset_class: str) -> str:
    # from config.env_loader import load_env
    # load_env(service_path=str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

    if asset_class == "INDEX":
        CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_FNO_DATABASE", "market_data")  # Use options database for FNO
        CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_INDEX_TABLE", "spot")  # Default table name
        return CLICKHOUSE_DATABASE, CLICKHOUSE_TABLE
    elif asset_class == "OPTION":
        CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_FNO_DATABASE", "market_data")  # Use options database for FNO
        CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_OPTION_TABLE", "options")  # Default table name
        return CLICKHOUSE_DATABASE, CLICKHOUSE_TABLE

    elif asset_class == "EQUITY":
        return "equity_data"
    elif asset_class == "CRYPTO":
        return "crypto_data"
    elif asset_class == "FOREX":
        return "forex_data"
    else:
        raise ValueError(f"Unsupported asset class: {asset_class}")