"""Storage modules for database and logging"""
from src.storage.db import Database
from src.storage.logger import setup_logger as _setup_logger

__all__ = ["Database", "get_db", "setup_logger"]


def get_db() -> Database:
    """Get database singleton instance."""
    from src.config import load_config

    config = load_config()
    return Database(config.database.path)
