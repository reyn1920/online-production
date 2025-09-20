# src/core/logging.py
import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with consistent formatting."""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
