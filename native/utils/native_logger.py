"""
Enhanced logging for native MPS pipeline.
Provides comprehensive logging with file output to logs/ directory.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON = True
except ImportError:
    HAS_JSON = False


def setup_native_logger(
    stage_name: str,
    movie_name: Optional[str] = None,
    log_level: str = "INFO",
    log_format: str = "text"
) -> logging.Logger:
    """
    Setup comprehensive logger for native MPS pipeline stages.
    
    Features:
    - Dual output: console (for monitoring) + file (for records)
    - Logs saved to logs/ directory with timestamps
    - Per-stage and per-movie log files
    - Supports both JSON and text formatting
    - Automatic log rotation support
    
    Args:
        stage_name: Name of the pipeline stage (e.g., 'demux', 'asr')
        movie_name: Optional movie identifier for per-movie logs
        log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_format: 'json' or 'text'
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_native_logger('asr', 'My_Movie_2024')
        >>> logger.info("Processing started")
        >>> logger.debug("Detailed processing info")
    """
    # Create unique logger name
    if movie_name:
        logger_name = f"native.{stage_name}.{movie_name}"
    else:
        logger_name = f"native.{stage_name}"
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers = []  # Clear existing handlers
    logger.propagate = False  # Don't propagate to root logger
    
    # Create formatters
    if log_format == "json" and HAS_JSON:
        # JSON formatter for structured logging
        console_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Text formatter for human-readable logs
        console_formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Console handler (simpler format for real-time monitoring)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Only INFO+ to console
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (detailed format for debugging)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create stage-specific log file
    if movie_name:
        log_filename = f"{stage_name}_{movie_name}_{timestamp}.log"
    else:
        log_filename = f"{stage_name}_{timestamp}.log"
    
    log_file = logs_dir / log_filename
    
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Capture all levels to file
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Log the initialization
    logger.debug(f"Logger initialized: {logger_name}")
    logger.debug(f"Log file: {log_file}")
    logger.debug(f"Log level: {log_level}")
    logger.debug(f"Log format: {log_format}")
    
    return logger


class NativePipelineLogger:
    """
    Enhanced class-based logger for native MPS pipeline.
    Provides comprehensive logging with performance tracking.
    """
    
    def __init__(
        self,
        stage_name: str,
        movie_name: Optional[str] = None,
        log_level: str = "INFO",
        log_format: str = "text"
    ):
        """
        Initialize native pipeline logger.
        
        Args:
            stage_name: Name of the pipeline stage
            movie_name: Optional movie identifier
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Format (json or text)
        """
        self.stage_name = stage_name
        self.movie_name = movie_name
        self.logger = setup_native_logger(stage_name, movie_name, log_level, log_format)
        self.start_time = datetime.now()
        
        # Log initialization
        self.info(f"{'='*60}")
        self.info(f"Native MPS Pipeline - Stage: {stage_name.upper()}")
        if movie_name:
            self.info(f"Movie: {movie_name}")
        self.info(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(f"{'='*60}")
    
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
    
    def log_stage_start(self, description: str = ""):
        """Log stage start with description."""
        self.info(f"▶️  Stage starting: {description}" if description else "▶️  Stage starting")
    
    def log_stage_end(self, success: bool = True):
        """Log stage end with duration."""
        duration = (datetime.now() - self.start_time).total_seconds()
        if success:
            self.info(f"✅ Stage completed successfully in {duration:.2f}s")
        else:
            self.error(f"❌ Stage failed after {duration:.2f}s")
        self.info(f"{'='*60}")
    
    def log_progress(self, current: int, total: int, item: str = "items"):
        """Log progress through a task."""
        percentage = (current / total * 100) if total > 0 else 0
        self.info(f"Progress: {current}/{total} {item} ({percentage:.1f}%)")
    
    def log_metric(self, name: str, value, unit: str = ""):
        """Log a metric or measurement."""
        unit_str = f" {unit}" if unit else ""
        self.info(f"📊 {name}: {value}{unit_str}")
    
    def log_file_operation(self, operation: str, path: Path, success: bool = True):
        """Log file operations."""
        status = "✓" if success else "✗"
        self.info(f"{status} {operation}: {path}")
    
    def log_model_load(self, model_name: str, device: str):
        """Log model loading."""
        self.info(f"🔧 Loading model: {model_name} on {device}")
    
    def log_processing(self, description: str, duration: Optional[float] = None):
        """Log processing step."""
        if duration:
            self.info(f"⚙️  {description} ({duration:.2f}s)")
        else:
            self.info(f"⚙️  {description}")


def create_session_log(session_name: str) -> Path:
    """
    Create a session log file for the entire pipeline run.
    
    Args:
        session_name: Name of the pipeline session (usually movie name)
    
    Returns:
        Path to the session log file
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_log = logs_dir / f"session_{session_name}_{timestamp}.log"
    
    return session_log
