from utillities import _month_path, _ensure_path, _write_parquet_file, _build_manifest, _manifest_path, _get_db_and_table
from config import get_logger
from config import get_symbol_mapping
from clients import ClickHouseClient
from queries import get_monthly_export_query
from config import load_env
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any
from pathlib import Path

logger = get_logger("provider")

# Load environment variables and initialize ClickHouse client
source_dir = Path(__file__).resolve().parents[1]

load_env(service_path=str(source_dir), logger=logger)
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 9000))
CLICKHOUSE_USERNAME = os.getenv("CLICKHOUSE_USERNAME", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "default")


def _create_fno_data(asset_class: str, symbol: str, year: int, month: int):
    """
    Create FNO (Futures and Options) data for the given symbol, year, and month
    by querying ClickHouse and saving as Parquet files.
    """
    folder_path = ["INDEX", "OPTION"]
    
    # Calculate date range for the given month
    start_date = datetime(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    for folder in folder_path:
        month_path = _month_path(folder, symbol)
        _ensure_path(month_path)

        file_path = month_path / f"{symbol}_{year}_{month:02d}.parquet"
        
        # Query data from ClickHouse using the template
        try:
            # Get the monthly export query from templates
            CLICKHOUSE_DATABASE, CLICKHOUSE_TABLE = _get_db_and_table(folder)  # Ensure we have the correct database and table for the asset class
            
            clickhouse_client = ClickHouseClient(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            user=CLICKHOUSE_USERNAME,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DATABASE,
            logger=logger
            )

            query = get_monthly_export_query(CLICKHOUSE_TABLE)
            query_symbol = get_symbol_mapping(asset_class, folder, symbol) or symbol  # Map symbol if needed

            params = {
                "symbol": query_symbol,  # Append "50" for index symbols if needed
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
            
            results = clickhouse_client.execute_query_with_params(query, params)
            
            columns = [c[0] for c in results[1]]
            results = results[0]  # Extract the actual data from the tuple returned by execute_query_with_params
            events = [dict(zip(columns, row))
            for row in results]

            # Convert results to list of dictionaries
            if results:

                # Write the parquet file with actual data
                file_meta = _write_parquet_file(file_path, events)
                
                # Build manifest
                manifest = _build_manifest([file_meta], [file_meta["symbol"]])
                manifest_path = _manifest_path(folder, symbol)
                manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
                logger.info(f"Created monthly parquet and manifest: {folder} for {symbol} {year}-{month:02d} with {len(events)} records")
            else:
                logger.warning(f"No data found for {symbol} {year}-{month:02d} in folder {folder}")
                # Still create empty file to maintain consistency
                file_meta = _write_parquet_file(file_path, [])
                manifest = _build_manifest([file_meta], ["UNKNOWN"])
                manifest_path = _manifest_path(folder, symbol)
                manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Failed to create FNO data for {symbol} {year}-{month:02d} in folder {folder}: {e}")
            raise

def _create_equity_data(symbol: str, year: int, month: int):
    pass

def _create_crypto_data(symbol: str, year: int, month: int):
    pass

def _create_forex_data(symbol: str, year: int, month: int):
    pass
