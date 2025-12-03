#!/usr/bin/env python3
"""

logger = get_logger(__name__)

Filename Parser for Movie Files

Parses movie filenames to extract title, year, and other metadata.
Handles various naming conventions for Bollywood movies.
"""

# Standard library
import re
from typing import NamedTuple, Optional


class ParsedFilename(NamedTuple):
    """Parsed filename components"""
    title: str
    year: Optional[int] = None
    quality: Optional[str] = None
    format: Optional[str] = None
    language: Optional[str] = None
    

def parse_filename(filename: str) -> ParsedFilename:
    """
    Parse movie filename to extract title and year.
    
    Handles formats like:
    - "Movie Name 2020.mp4"
    - "Movie Name (2020).mp4"
    - "Movie.Name.2020.1080p.mkv"
    - "Movie_Name_2020_Hindi.mp4"
    
    Args:
        filename: Movie filename or path
        
    Returns:
        ParsedFilename with title, year, and other metadata
        
    Examples:
        >>> parse_filename("Dilwale Dulhania Le Jayenge 1995.mp4")
        ParsedFilename(title='Dilwale Dulhania Le Jayenge', year=1995, ...)
        
        >>> parse_filename("3 Idiots (2009) 1080p.mkv")
        ParsedFilename(title='3 Idiots', year=2009, quality='1080p', ...)
    """
    from pathlib import Path

# Local
from shared.logger import get_logger
    
    # Get basename without extension
    basename = Path(filename).stem
    
    # Initialize variables
    title = basename
    year = None
    quality = None
    format_type = None
    language = None
    
    # Extract year - look for 4-digit year (1900-2099)
    year_patterns = [
        r'\((\d{4})\)',      # (2020)
        r'[\s\._-](\d{4})[\s\._-]',  # .2020. or _2020_
        r'[\s\._-](\d{4})$', # .2020 at end
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, basename)
        if match:
            potential_year = int(match.group(1))
            if 1900 <= potential_year <= 2099:
                year = potential_year
                # Remove year from title
                title = re.sub(pattern, ' ', basename).strip()
                break
    
    # If year still not found, try at the end
    if not year:
        match = re.search(r'(\d{4})$', basename)
        if match:
            potential_year = int(match.group(1))
            if 1900 <= potential_year <= 2099:
                year = potential_year
                title = basename[:match.start()].strip()
    
    # Extract quality (1080p, 720p, 4K, etc.)
    quality_match = re.search(r'(\d+p|4K|HD|UHD|BluRay|BRRip|WEB-DL|HDRip)', basename, re.IGNORECASE)
    if quality_match:
        quality = quality_match.group(1)
        title = title.replace(quality_match.group(0), '').strip()
    
    # Extract language
    language_match = re.search(r'(Hindi|English|Tamil|Telugu|Bengali|Marathi|Punjabi|Gujarati)', basename, re.IGNORECASE)
    if language_match:
        language = language_match.group(1)
        title = title.replace(language_match.group(0), '').strip()
    
    # Clean up title
    # Replace separators with spaces
    title = re.sub(r'[_\.]', ' ', title)
    # Remove extra spaces
    title = re.sub(r'\s+', ' ', title)
    # Remove common tags
    title = re.sub(r'\b(1080p|720p|4K|HD|UHD|BluRay|BRRip|WEB-DL|HDRip|x264|x265|HEVC|AAC|AC3)\b', '', title, flags=re.IGNORECASE)
    # Final cleanup
    title = title.strip(' -_.')
    
    return ParsedFilename(
        title=title,
        year=year,
        quality=quality,
        format=format_type,
        language=language
    )


def format_title_for_display(parsed: ParsedFilename) -> str:
    """
    Format parsed filename for display.
    
    Args:
        parsed: ParsedFilename object
        
    Returns:
        Formatted title string
        
    Example:
        >>> p = parse_filename("Dilwale Dulhania Le Jayenge 1995.mp4")
        >>> format_title_for_display(p)
        'Dilwale Dulhania Le Jayenge (1995)'
    """
    if parsed.year:
        return f"{parsed.title} ({parsed.year})"
    return parsed.title


def format_title_for_filename(parsed: ParsedFilename) -> str:
    """
    Format parsed filename for use in filenames (safe characters).
    
    Args:
        parsed: ParsedFilename object
        
    Returns:
        Filename-safe title string
        
    Example:
        >>> p = parse_filename("Dilwale Dulhania Le Jayenge 1995.mp4")
        >>> format_title_for_filename(p)
        'Dilwale_Dulhania_Le_Jayenge_1995'
    """
    safe_title = re.sub(r'[^\w\s-]', '', parsed.title)
    safe_title = re.sub(r'[\s-]+', '_', safe_title)
    
    if parsed.year:
        return f"{safe_title}_{parsed.year}"
    return safe_title


if __name__ == "__main__":
    # Test cases
    test_files = [
        "Dilwale Dulhania Le Jayenge 1995.mp4",
        "3 Idiots (2009) 1080p.mkv",
        "Dil Chahta Hai 2001 Hindi.mp4",
        "Zindagi_Na_Milegi_Dobara_2011_720p.mp4",
        "Kabhi Khushi Kabhie Gham 2001.avi",
        "Jaane Tu Ya Jaane Na 2008.mp4",
    ]
    
    logger.info("Filename Parser Test Cases:")
    logger.info("=" * 80)
    for filename in test_files:
        parsed = parse_filename(filename)
        logger.info(f"\nInput:   {filename}")
        logger.info(f"Title:   {parsed.title}")
        logger.info(f"Year:    {parsed.year}")
        logger.info(f"Display: {format_title_for_display(parsed)}")
        logger.info(f"Safe:    {format_title_for_filename(parsed)}")
