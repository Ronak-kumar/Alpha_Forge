import sys
import os
from pathlib import Path

# Ensure local source path is importable
root_dir = Path(__file__).resolve().parents[3]
source_dir = Path(__file__).resolve().parents[0]
sys.path.append(str(root_dir))
sys.path.append(str(source_dir))

from config.env_loader import load_env
from apps.data_service.src.config.logger import get_logger
from clients.clickhouse_client import ClickHouseClient
from api.app import app


# Initialize logger
logger = get_logger("main")

# Load data service env file
load_env(service_path=str(source_dir), logger=logger)

host = os.getenv("CLICKHOUSE_HOST", "localhost")
port = int(os.getenv("CLICKHOUSE_PORT", 9000))
username = os.getenv("CLICKHOUSE_USERNAME", "default")
password = os.getenv("CLICKHOUSE_PASSWORD", "default")
database = os.getenv("CLICKHOUSE_CRYPTO_DATABASE", "default")
clickhouse_client = ClickHouseClient(host=host, port=port, user=username, password=password, database=database, logger=logger)

# try:
#     _ = clickhouse_client.execute_query("SELECT * FROM spot LIMIT 5")
#     logger.info("Data service initialized with sample ClickHouse query")
# except Exception as exc:
#     logger.warning(f"ClickHouse initialization skipped: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)))

