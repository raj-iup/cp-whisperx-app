"""
Shared utilities for all pipeline containers.
Cross-platform compatible (Windows, Linux, macOS).
"""
import json
import re
import platform
from pathlib import Path
from typing import Dict, Any, Optional


def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        import os
        os.fsync(f.fileno())


def load_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load data from JSON file."""
    if not filepath.exists():
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content or content.strip() == '':
            return None
        return json.loads(content)


def parse_filename(filename: str) -> Dict[str, str]:
    """
    Parse movie filename to extract title and year.
    
    Examples:
        "Jaane Tu Ya Jaane Na 2006.mp4" -> {"title": "Jaane Tu Ya Jaane Na", "year": "2006"}
        "Movie Title (2020).mkv" -> {"title": "Movie Title", "year": "2020"}
    """
    # Remove extension
    name = Path(filename).stem
    
    # Try to extract year
    year_match = re.search(r'[(\[]?(\d{4})[)\]]?', name)
    year = year_match.group(1) if year_match else None
    
    # Remove year from title
    if year:
        title = re.sub(r'[(\[]?' + year + r'[)\]]?', '', name).strip()
    else:
        title = name
    
    # Clean up title
    title = re.sub(r'[._-]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return {"title": title, "year": year}


def sanitize_dirname(name: str) -> str:
    """
    Sanitize a string to be used as a directory name.
    
    Args:
        name: String to sanitize
    
    Returns:
        Safe directory name
    """
    # Replace spaces with underscores
    safe = name.replace(' ', '_')
    
    # Remove or replace unsafe characters
    safe = re.sub(r'[^\w\-_]', '', safe)
    
    # Remove multiple underscores
    safe = re.sub(r'_+', '_', safe)
    
    # Remove leading/trailing underscores
    safe = safe.strip('_')
    
    return safe


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == 'Windows'


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == 'Linux'


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == 'Darwin'


def normalize_path(path_str: str) -> Path:
    """
    Normalize path for current platform.
    Handles Windows, Linux, and macOS paths.
    
    Args:
        path_str: Path string (may contain mixed separators)
    
    Returns:
        Normalized Path object
    """
    # Convert to Path object (handles conversion automatically)
    path = Path(path_str)
    
    # Resolve to absolute path if needed
    if not path.is_absolute():
        path = path.resolve()
    
    return path


def get_platform_info() -> Dict[str, str]:
    """
    Get platform information for logging and diagnostics.
    
    Returns:
        Dictionary with platform details
    """
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }
    
    return safe


def get_movie_dir(input_file: Path, output_root: Path) -> Path:
    """
    Get or create movie-specific output directory.
    
    Args:
        input_file: Input video file path
        output_root: Root output directory
    
    Returns:
        Path to movie-specific directory
    """
    # Parse filename
    file_info = parse_filename(input_file.name)
    
    # Create directory name
    if file_info['year']:
        dir_name = f"{sanitize_dirname(file_info['title'])}_{file_info['year']}"
    else:
        dir_name = sanitize_dirname(file_info['title'])
    
    # Create and return path
    movie_dir = output_root / dir_name
    movie_dir.mkdir(parents=True, exist_ok=True)
    
    return movie_dir


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (HH:MM:SS,mmm).
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
