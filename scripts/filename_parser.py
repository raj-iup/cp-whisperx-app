"""
filename_parser.py - Parse movie title and year from filename

Handles noisy filenames like:
- JO_JEETA_WOHI_SIKANDAR_1992.mp4
- Satte_Pe_Satta_(1982).mp4
- Movie.Name.2010.1080p.BluRay.mp4
"""

import re
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ParsedFilename:
    """Result of filename parsing"""
    title: str
    year: Optional[int]
    original_filename: str
    sanitized_title: str  # Title with underscores/spaces normalized


def parse_filename(filepath: str) -> ParsedFilename:
    """
    Parse movie title and year from filename

    Args:
        filepath: Path to video file

    Returns:
        ParsedFilename with title, year, and sanitized title

    Examples:
        >>> parse_filename("JO_JEETA_WOHI_SIKANDAR_1992.mp4")
        ParsedFilename(title="Jo Jeeta Wohi Sikandar", year=1992, ...)

        >>> parse_filename("Satte_Pe_Satta_(1982).mp4")
        ParsedFilename(title="Satte Pe Satta", year=1982, ...)

        >>> parse_filename("Movie.Name.2010.1080p.BluRay.mp4")
        ParsedFilename(title="Movie Name", year=2010, ...)
    """
    path = Path(filepath)
    filename = path.stem  # Remove extension

    original_filename = path.name

    # Extract year (4 digits, typically 1950-2029)
    year_match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', filename)
    year = int(year_match.group(1)) if year_match else None

    # Remove year from filename
    if year:
        filename = filename.replace(str(year), '')

    # Remove common video metadata patterns
    # E.g., 1080p, BluRay, WEB-DL, x264, etc.
    patterns_to_remove = [
        r'\b(720p|1080p|2160p|4K)\b',
        r'\b(BluRay|BRRip|WEB-DL|WEBRip|DVDRip|HDTV)\b',
        r'\b(x264|x265|h264|h265|HEVC)\b',
        r'\b(AAC|AC3|DTS|DD5\.1)\b',
        r'\b(HINDI|ENGLISH|ENG|HIN)\b',
        r'\b(EXTENDED|UNRATED|DIRECTORS\.CUT)\b',
        r'\[.*?\]',  # Remove anything in brackets
        r'\(.*?\)',  # Remove anything in parentheses (except year, already removed)
    ]

    for pattern in patterns_to_remove:
        filename = re.sub(pattern, ' ', filename, flags=re.IGNORECASE)

    # Replace separators with spaces
    filename = re.sub(r'[._\-]+', ' ', filename)

    # Clean up multiple spaces
    filename = re.sub(r'\s+', ' ', filename).strip()

    # Title case
    title = filename.title()

    # Sanitized title (for directory names, etc.)
    sanitized_title = re.sub(r'\s+', '_', title)

    return ParsedFilename(
        title=title,
        year=year,
        original_filename=original_filename,
        sanitized_title=sanitized_title
    )


def infer_movie_name(filepath: str) -> str:
    """
    Infer movie name from filepath (convenience function)

    Args:
        filepath: Path to video file

    Returns:
        Movie title as string
    """
    parsed = parse_filename(filepath)
    if parsed.year:
        return f"{parsed.title} ({parsed.year})"
    return parsed.title
