import sys
from pathlib import Path
import os
import FastAPI





# Add root directory to Python path so we can import from 'config'
root_dir = Path(__file__).resolve().parents[3]
sys.path.append(str(root_dir))

from config.env_loader import load_env
from apps.data_service.src.config.logger import get_logger
from apps.data_service.src.clients.clickhouse_client import ClickHouseClient


# Initialize logger
logger = get_logger("main")

# Load data service env file
env_loaded = load_env(service_path=r"D:\Development\Coding_Projects\Main_projects\Alpha_Forge_2\Alpha_Forge\apps\data_service\src", logger=logger)

host  = os.getenv("CLICKHOUSE_HOST", "localhost")
port = int(os.getenv("CLICKHOUSE_PORT", 9000))
username = os.getenv("CLICKHOUSE_USERNAME", "default")
password = os.getenv("CLICKHOUSE_PASSWORD", "default")
databse = os.getenv("CLICKHOUSE_CRYPTO_DATABASE", "default")
clickhouse_client = ClickHouseClient(host=host, port=port, user=username, password=password, database=databse, logger=logger)
result = clickhouse_client.execute_query("SELECT * FROM spot LIMIT 5")
logger.info("Data service initialized")

