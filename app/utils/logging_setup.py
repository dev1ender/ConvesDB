"""
Logging setup utilities.
"""
import logging
import os
import sys
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

# Unicode icons for logging
TICK_ICON = '\u2705'  # ✅
CROSS_ICON = '\u274C'  # ❌


def setup_logging_from_config(logging_config: Optional[Dict[str, Any]] = None) -> None:
    """
    Set up logging using a configuration dictionary (from YAML config).
    Args:
        logging_config: Dict with logging options (level, console_output, file_output, log_dir, file_name_pattern, format, date_format, max_file_size_mb, max_files)
    """
    if logging_config is None:
        logging_config = {}

    level = getattr(logging, str(logging_config.get("level", "INFO")).upper(), logging.INFO)
    console_output = logging_config.get("console_output", True)
    file_output = logging_config.get("file_output", False)
    log_dir = logging_config.get("log_dir", "logs")
    file_name_pattern = logging_config.get("file_name_pattern", "app_%Y%m%d.log")
    log_format = logging_config.get("format", "%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    date_format = logging_config.get("date_format", "%Y-%m-%d %H:%M:%S")
    max_file_size_mb = logging_config.get("max_file_size_mb", 10)
    max_files = logging_config.get("max_files", 5)

    formatter = logging.Formatter(log_format, datefmt=date_format)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if file_output:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        from datetime import datetime
        log_file = os.path.join(log_dir, datetime.now().strftime(file_name_pattern))
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=max_files
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    logging.info(f"Logging initialized (level={logging.getLevelName(level)}, console={console_output}, file={file_output})")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name) 