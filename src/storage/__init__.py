"""Storage modules for database and logging"""
from src.storage.db import Database
from src.storage.logger import setup_logger


def get_db() -> Database:
    """Get database singleton instance."""
    from src.config import load_config

    config = load_config()
    return Database(config.database.path)
