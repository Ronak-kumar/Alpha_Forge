from pathlib import Path
from dotenv import load_dotenv


def load_env(env_filename: str = ".env", service_path: str = None, logger=None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_filename: Name of the env file (default: ".env")
        service_path: Optional path to a service folder. If provided, looks for .env in that folder.
                     If not provided, looks in the root project folder.
        logger: Optional logger instance for logging output
    
    Returns:
        True if loaded successfully, False otherwise.
    """
    if service_path:
        env_path = Path(service_path) / env_filename
    else:
        # Root project .env
        env_path = Path(__file__).resolve().parent.parent / env_filename
    
    if not env_path.exists():
        if logger:
            logger.warning("Env file not found at %s", env_path)
        return False

    load_dotenv(dotenv_path=env_path)
    if logger:
        logger.info("Loaded env from %s", env_path)
    return True
