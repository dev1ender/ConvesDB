"""
Logging setup for the NLP-to-SQL application.
Configures logging for all application components based on config.yml settings.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import logging.handlers

def setup_logging(log_level: str = "INFO", 
                 log_file: Optional[str] = None,
                 console_output: bool = True,
                 log_format: Optional[str] = None,
                 date_format: Optional[str] = None,
                 max_file_size_mb: int = 10,
                 max_files: int = 5) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Path to log file. If None, no file logging.
        console_output: Whether to output logs to console
        log_format: Format string for log messages
        date_format: Format string for dates in log messages
        max_file_size_mb: Maximum size of each log file in MB before rotation
        max_files: Maximum number of rotated log files to keep
        
    Returns:
        Root logger configured with handlers
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Define formatter with timestamp and module info
    if log_format is None:
        log_format = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    
    if date_format is None:
        date_format = '%Y-%m-%d %H:%M:%S'
        
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        # Use RotatingFileHandler instead of FileHandler for log rotation
        max_bytes = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=max_files
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Log startup message
    logger.info(f"Logging initialized at level {log_level}")
    
    return logger

def setup_logging_from_config(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging based on application configuration.
    
    Args:
        config: Application configuration dictionary
    
    Returns:
        Configured root logger
    """
    # Get logging configuration
    logging_config = config.get("logging", {})
    
    # Get app log level if no specific logging level is set
    log_level = logging_config.get("level") or config.get("app", {}).get("log_level", "info")
    
    # Get console output preference
    console_output = logging_config.get("console_output", True)
    
    # Set up file logging if enabled
    log_file = None
    if logging_config.get("file_output", False):
        log_dir = logging_config.get("log_dir", "logs")
        file_pattern = logging_config.get("file_name_pattern", "app_%Y%m%d.log")
        
        # Format the filename with current date
        try:
            log_filename = datetime.now().strftime(file_pattern)
        except Exception:
            log_filename = "app.log"
            
        log_file = os.path.join(log_dir, log_filename)
    
    # Get formatter settings
    log_format = logging_config.get("format", None)
    date_format = logging_config.get("date_format", None)
    
    # Get rotation settings
    max_file_size_mb = logging_config.get("max_file_size_mb", 10)
    max_files = logging_config.get("max_files", 5)
    
    # Set up logging
    return setup_logging(
        log_level=log_level, 
        log_file=log_file,
        console_output=console_output,
        log_format=log_format,
        date_format=date_format,
        max_file_size_mb=max_file_size_mb,
        max_files=max_files
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name for the logger
        
    Returns:
        Logger instance for the module
    """
    return logging.getLogger(name) 