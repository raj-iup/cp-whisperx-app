"""
Shared logging utilities for all pipeline containers.
Provides consistent logging across all steps.

This is the SINGLE SOURCE OF TRUTH for all logging in cp-whisperx-app.
Use this module for all Python scripts, Docker containers, and pipeline stages.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from pythonjsonlogger import jsonlogger


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_format: str = "json",
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_dir: str = "/app/logs"
) -> logging.Logger:
    """
    Setup logger for pipeline step.
    
    Args:
        name: Logger name (step name)
        log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_format: json or text
        log_to_console: Log to stdout
        log_to_file: Log to file
        log_dir: Directory for log files
    
    Returns:
        Configured logger instance
    
    Example:
        >>> from logger import setup_logger
        >>> logger = setup_logger("demux", log_level="INFO", log_format="text")
        >>> logger.info("Starting demux process")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers = []  # Clear existing handlers
    
    # Create formatters
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{name}_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class PipelineLogger:
    """
    Class-based logger wrapper for backward compatibility.
    Provides the same interface as scripts/logger.py but uses setup_logger internally.
    
    This class is provided for compatibility with existing code that uses PipelineLogger.
    New code should use setup_logger() directly.
    
    Example:
        >>> from logger import PipelineLogger
        >>> logger = PipelineLogger("asr")
        >>> logger.info("Starting ASR processing")
    """
    
    def __init__(
        self, 
        module_name: str, 
        log_file: Optional[Path] = None,
        log_level: str = "INFO",
        log_format: str = "text"
    ):
        """
        Initialize PipelineLogger.
        
        Args:
            module_name: Name of the module (e.g., "asr", "diarization")
            log_file: Optional specific log file path
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Format (json or text)
        """
        self.module_name = module_name
        
        if log_file:
            # Use specific log file
            log_dir = str(log_file.parent)
            self.logger = setup_logger(
                module_name,
                log_level=log_level,
                log_format=log_format,
                log_to_console=True,
                log_to_file=True,
                log_dir=log_dir
            )
        else:
            # Use default logging setup
            self.logger = setup_logger(
                module_name,
                log_level=log_level,
                log_format=log_format,
                log_to_console=True,
                log_to_file=True,
                log_dir="/app/logs"
            )
    
    def debug(self, msg: str):
        """Log debug message."""
        self.logger.debug(msg)
    
    def info(self, msg: str):
        """Log info message."""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Log warning message."""
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """Log error message."""
        self.logger.error(msg)
    
    def critical(self, msg: str):
        """Log critical message."""
        self.logger.critical(msg)
