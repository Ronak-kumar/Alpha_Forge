import yaml
from pathlib import Path

source_file = Path(__file__).resolve().parents[0] / "settings.yaml"

with open(source_file, "r") as f:
    config = yaml.safe_load(f)


def get_symbol_mapping(asset_class: str, instrument_type: str, symbol: str) -> str:
    return config.get(asset_class, {}).get(symbol, {}).get(instrument_type, symbol)