"""
logger.py - DEPRECATED - Use shared/logger.py instead

This module is kept for backward compatibility only.
All new code should import from shared.logger directly.

DEPRECATED: This will be removed in a future version.
"""
import warnings
from pathlib import Path
from typing import Optional

# Import from the canonical location
import sys
sys.path.insert(0, '/app/shared')
from logger import PipelineLogger as SharedPipelineLogger, setup_logger


# Issue deprecation warning
warnings.warn(
    "scripts.logger is deprecated. Import from shared.logger instead:\n"
    "  OLD: from scripts.logger import PipelineLogger\n"
    "  NEW: from logger import PipelineLogger",
    DeprecationWarning,
    stacklevel=2
)


class PipelineLogger(SharedPipelineLogger):
    """
    DEPRECATED: Use shared.logger.PipelineLogger instead.
    
    This class is a thin wrapper for backward compatibility.
    """
    pass


def create_logger(module_name: str, log_dir: Optional[Path] = None):
    """
    DEPRECATED: Use shared.logger.setup_logger() or PipelineLogger instead.
    
    Create a logger for a pipeline module.
    
    Args:
        module_name: Name of the module (e.g., "filename_parser")
        log_dir: Optional timestamped log directory
    
    Returns:
        PipelineLogger instance
    """
    warnings.warn(
        "create_logger() is deprecated. Use setup_logger() or PipelineLogger instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    if log_dir:
        log_file = log_dir / f"{module_name}.log"
        return PipelineLogger(module_name, log_file=log_file)
    else:
        return PipelineLogger(module_name)


def create_timestamped_log_dir(log_root: Path) -> Path:
    """
    Create timestamped log directory.
    
    Args:
        log_root: Root log directory (e.g., ./logs)
    
    Returns:
        Path to timestamped directory (e.g., ./logs/20250127_143022)
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = log_root / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
