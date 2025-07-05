import sys
from pathlib import Path

from loguru import logger


log_path = Path(__file__).resolve().parent.parent.parent / "logs" / "mail-service"
log_path.mkdir(exist_ok=True, parents=True)

logger.remove()


def formatter(record):
    return "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | {message:<50} | <cyan>{name}:{function}:{line}</cyan>\n"


logger.add(
    sys.stdout,
    level="DEBUG",
    format=formatter,
    colorize=True,
)

logger.add(
    log_path / "debug.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
    encoding="utf-8",
    format=formatter,
)

logger.add(
    log_path / "info.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="INFO",
    encoding="utf-8",
    format=formatter,
)

logger.add(
    log_path / "warning.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="WARNING",
    encoding="utf-8",
    format=formatter,
)
