"""
Logging configuration using Loguru.
Provides structured logging with context and formatting.
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings

# Remove default handler
logger.remove()

# Console handler with custom format
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)

# File handler for errors
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "backbone_ai_error.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="10 MB",
    retention="1 week",
    compression="zip",
)

# File handler for all logs in development
if settings.is_development:
    logger.add(
        log_dir / "backbone_ai_debug.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="3 days",
        compression="zip",
    )


def get_logger(name: str):
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)
