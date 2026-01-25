"""
日志管理模块
"""
from pathlib import Path
from loguru import logger


def setup_logger(
    log_file: str = "data/logs/app.log",
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
):
    """配置日志"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()  # 移除默认处理器

    logger.add(
        log_file,
        level=level,
        rotation=rotation,
        retention=retention,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>",
        encoding="utf-8",
    )

    # 同时输出到控制台
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level,
    )

    return logger
