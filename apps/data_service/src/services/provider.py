from apps.data_service.src.helpers.utill import _month_path, _ensure_path, _write_parquet_file, _build_manifest, _manifest_path
import json


def _create_fno_data(symbol: str, year: int, month: int):
    folder_path = ["INDEX", "OPTION"]
    for folder in folder_path:
        month_path = _month_path(folder, symbol)
        _ensure_path(month_path)

        file_path = month_path / f"{symbol}_{year}_{month:02d}.parquet"
        file_meta = _write_parquet_file(file_path)
        manifest = _build_manifest([file_meta], [file_meta["symbol"]])
        manifest_path = _manifest_path(folder, symbol)
        manifest_path.write_text(json.dumps(manifest, indent=2))


def _create_equity_data(symbol: str, year: int, month: int):
    pass

def _create_crypto_data(symbol: str, year: int, month: int):
    pass

def _create_forex_data(symbol: str, year: int, month: int):
    pass