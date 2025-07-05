import sys
from loguru import logger


logger.remove()


def formatter(record):
    return "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | {message:<50} | <cyan>{name}:{function}:{line}</cyan>\n"


logger.add(
    sys.stdout,
    level="DEBUG",
    format=formatter,
    colorize=True,
)
