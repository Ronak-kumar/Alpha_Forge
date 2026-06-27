import os
# from pathlib import Path
# import sys

# Ensure local source path is importable
## Main project core path integration ##
# root_dir = Path(__file__).resolve().parents[3]
# sys.path.append(str(root_dir))

## Current service path integration ##
# source_dir = Path(__file__).resolve().parents[0]
# sys.path.append(str(source_dir))

from config.logger import get_logger
from api.app import app

# Initialize logger
logger = get_logger("[Data_Service][main]")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)))

