"""
Centralized logging configuration for the entire project using Loguru.
Logs are fully JSON-serialized and ready to be ingested by modern SIEMs or log aggregators (e.g., Datadog, ELK).

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__, headline="main.py")
    logger.info("Started data download...")
"""

import sys

from loguru import logger

from src.constants import LOGS_DIR

LOG_FILE = LOGS_DIR / "running_logs.log"

# Configure loguru: remove default handler, add console handler and JSON file handler
logger.remove()

# Console handler (human-readable)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
    enqueue=True,
)

# File handler (JSON serialized)
logger.add(
    LOG_FILE,
    serialize=True,
    rotation="5 MB",
    retention=5,
    enqueue=True,
)


from typing import Any

def get_logger(name: str | None = None, headline: str | None = None) -> Any:
    """
    Returns a configured loguru logger.
    Adds an optional headline section to separate logs per script.

    Args:
        name (Optional[str]): Optional logger name, typically __name__.
        headline (Optional[str]): Optional headline for visual separation.

    Returns:
        loguru.Logger: Configured logger instance.
    """
    bound_logger = logger.bind(custom_name=name) if name else logger

    if headline:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n")
        bound_logger.info(f"=== START: {headline} ===")

    return bound_logger
