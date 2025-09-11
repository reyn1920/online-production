import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(log_dir="logs", file_name="trae_ai.log", level = logging.INFO):
    """
    Configures and returns a centralized, rotating logger.
    """
    os.makedirs(log_dir, exist_ok = True)
    log_file_path = os.path.join(log_dir, file_name)

    # Prevent adding handlers multiple times in the same session
    logger = logging.getLogger("TRAE_AI")
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Create a rotating file handler
    # Keeps 5 log files, each up to 10MB
    handler = RotatingFileHandler(
        log_file_path, maxBytes = 10 * 1024 * 1024, backupCount = 5
    )

    # Create a standard log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger
