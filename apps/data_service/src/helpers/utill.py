
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_BASE = Path(__file__).resolve().parents[1] / "cache"
MANIFEST_NAME = "manifest.json"


def _month_path(segment: str, symbol: str) -> Path:
    return DATA_BASE / segment / symbol


def _manifest_path(segment: str, symbol: str) -> Path:
    return _month_path(segment, symbol) / MANIFEST_NAME


def _ensure_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)