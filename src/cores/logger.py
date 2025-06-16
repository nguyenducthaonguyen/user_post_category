import logging
from logging.handlers import RotatingFileHandler
import sys
import os


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOG_FORMAT = os.getenv(
    "LOG_FORMAT", "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    if not logger.hasHandlers():
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        # Rotating file handler (5 files max 10MB each)
        file_handler = RotatingFileHandler(
            "logs/access.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
