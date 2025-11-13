"""
Shared logging utilities for all pipeline containers.
Provides consistent logging across all steps.

This is the SINGLE SOURCE OF TRUTH for all logging in cp-whisperx-app.
Use this module for all Python scripts, Docker containers, and pipeline stages.
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from pythonjsonlogger import jsonlogger


# Stage order mapping for log file prefixes
STAGE_ORDER = {
    "orchestrator": 0,
    "demux": 1,
    "tmdb": 2,
    "pre-ner": 3,
    "pre_ner": 3,
    "silero-vad": 4,
    "silero_vad": 4,
    "pyannote-vad": 5,
    "pyannote_vad": 5,
    "diarization": 6,
    "asr": 7,
    "glossary-builder": 8,
    "glossary_builder": 8,
    "second-pass-translation": 9,
    "second_pass_translation": 9,
    "lyrics-detection": 10,
    "lyrics_detection": 10,
    "post-ner": 11,
    "post_ner": 11,
    "subtitle-gen": 12,
    "subtitle_gen": 12,
    "mux": 13,
    "finalize": 14,
}


def get_stage_log_filename(stage_name: str, timestamp: Optional[str] = None) -> str:
    """
    Generate a stage-prefixed log filename.
    
    Args:
        stage_name: Name of the stage (e.g., "asr", "diarization")
        timestamp: Optional timestamp string (defaults to current time)
    
    Returns:
        Formatted log filename with stage number prefix (e.g., "07_asr_20251101_120000.log")
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    stage_num = STAGE_ORDER.get(stage_name, 99)
    return f"{stage_num:02d}_{stage_name}_{timestamp}.log"


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
        # Use UTF-8 encoding for console output to handle Unicode characters on Windows
        import io
        if sys.platform == 'win32':
            # Reconfigure stdout to use UTF-8 encoding with error handling
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, OSError):
                # Fallback for older Python or if reconfigure fails
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Check for existing log file for this stage today
        stage_num = STAGE_ORDER.get(name, 99)
        prefix = f"{stage_num:02d}_{name}_"
        today = datetime.now().strftime("%Y%m%d")
        
        # Look for existing log file from today
        existing_logs = list(log_path.glob(f"{prefix}{today}_*.log"))
        
        if existing_logs:
            # Reuse the most recent log file
            log_file = sorted(existing_logs)[-1]
        else:
            # Create new log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_path / get_stage_log_filename(name, timestamp)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')  # Append mode with UTF-8
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
        
        # Try to load log level from config/environment if not explicitly set
        if log_level == "INFO":
            try:
                from config import load_config
                config = load_config()
                if hasattr(config, 'log_level') and config.log_level:
                    log_level = config.log_level.upper()
            except:
                pass
        
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
            # Load log directory from config if available
            try:
                from config import load_config
                config = load_config()
                log_dir = config.log_root
            except:
                # Fallback to default if config loading fails
                log_dir = "/app/logs"
            
            self.logger = setup_logger(
                module_name,
                log_level=log_level,
                log_format=log_format,
                log_to_console=True,
                log_to_file=True,
                log_dir=log_dir
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
