import sys
from loguru import logger


def setup_logging() -> None:
    logger.remove()

    try:
        from .. import constants

        log_level = getattr(constants, "LOG_LEVEL", "INFO").upper()
    except ImportError:
        log_level = "INFO"

    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )


def get_logger():
    return logger
