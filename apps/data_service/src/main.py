import sys
from pathlib import Path

# Add root directory to Python path so we can import from 'config'
root_dir = Path(__file__).resolve().parents[3]
sys.path.append(str(root_dir))

from config.env_loader import load_env
from apps.data_service.src.config.logger import get_logger

# Initialize logger
logger = get_logger("main")

# Load data service env file
env_loaded = load_env(service_path=r"D:\Development\Coding_Projects\Main_projects\Alpha_Forge_2\Alpha_Forge\apps\data_service\src", logger=logger)
logger.info("Data service initialized")

