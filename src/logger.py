"""
Logger module for the trading bot.
Handles logging configuration and provides logging utilities.
"""
import logging
import os
from typing import Optional


def setup_logger(name: str = "trading_bot", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name (str): Name of the logger. Defaults to "trading_bot".
        log_level (int): Logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent adding handlers if they already exist
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"{name}.log"),
            encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
            )
        )
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger()
