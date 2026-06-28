from typing import Any, Dict

from config import get_logger
from .provider import _create_fno_data, _create_equity_data, _create_crypto_data, _create_forex_data

logger = get_logger("api.monthly")


async def create_monthly_data(asset_class: str, year: int, month: int, symbol: str, exchange: str) -> Dict[str, Any]:
    if asset_class == "FNO":
        _create_fno_data(asset_class, symbol, year, month)
        logger.info(f"Created monthly parquet and metadata: {asset_class} for {symbol} {year}-{month:02d}")

    elif asset_class == "EQUITY":
        _create_equity_data(symbol, year, month)
        logger.info(f"Created monthly parquet and metadata: {asset_class} for {symbol} {year}-{month:02d}")
    elif asset_class == "CRYPTO":
        _create_crypto_data(symbol, year, month)
        logger.info(f"Created monthly parquet and metadata: {asset_class} for {symbol} {year}-{month:02d}")
    elif asset_class == "FOREX":
        _create_forex_data(symbol, year, month)

    return True