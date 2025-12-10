"""
Log path utilities for centralized log management.

Per AD-012: All log files must be organized in logs/ directory.
"""
from pathlib import Path
from datetime import datetime
from typing import Literal

LogCategory = Literal["testing", "debug", "pipeline"]


def get_log_path(
    category: LogCategory,
    purpose: str,
    detail: str = ""
) -> Path:
    """
    Get standardized log file path in logs/ directory.
    
    Args:
        category: "testing", "debug", or "pipeline"
        purpose: Feature/test being logged (e.g., "transcribe", "mlx")
        detail: Optional additional context (e.g., "validation", "error")
        
    Returns:
        Path to log file in logs/ directory with timestamp
        
    Examples:
        >>> get_log_path("testing", "transcribe", "mlx")
        Path('logs/testing/manual/20251208_130045_transcribe_mlx.log')
        
        >>> get_log_path("debug", "alignment")
        Path('logs/debug/20251208_130045_alignment.log')
        
        >>> get_log_path("pipeline", "job-123")
        Path('logs/pipeline/2025-12-08/20251208_130045_job-123.log')
    
    Note:
        Automatically creates parent directories if they don't exist.
    """
    # Get project root (2 levels up from shared/)
    project_root = Path(__file__).parent.parent
    
    # Build timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Build filename
    filename = f"{timestamp}_{purpose}"
    if detail:
        filename += f"_{detail}"
    filename += ".log"
    
    # Build directory path based on category
    if category == "testing":
        log_dir = project_root / "logs" / category / "manual"
    elif category == "pipeline":
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_dir = project_root / "logs" / category / date_str
    else:  # debug
        log_dir = project_root / "logs" / category
    
    # Create directory if needed
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir / filename


def get_existing_log_path(log_file: Path) -> Path:
    """
    Get the new location for an existing log file.
    
    Args:
        log_file: Existing log file path (in project root)
        
    Returns:
        New path in logs/testing/manual/ directory
        
    Example:
        >>> get_existing_log_path(Path("test-mlx.log"))
        Path('logs/testing/manual/test-mlx.log')
    """
    project_root = Path(__file__).parent.parent
    new_dir = project_root / "logs" / "testing" / "manual"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir / log_file.name
