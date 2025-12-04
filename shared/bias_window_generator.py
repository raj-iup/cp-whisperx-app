#!/usr/bin/env python3
"""
Bias Window Generator - Context-Aware Prompting for WhisperX

Provides glossary-based bias prompting to improve ASR accuracy for:
- Character names (Bollywood/Indic media)
- Cultural terms (Hindi idioms, relationship terms)
- Domain-specific terminology
- Technical jargon

Part of Phase 5: Advanced Features (Context-Aware Subtitles)
See: docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md § Phase 5

Module: shared/bias_window_generator.py
Status: ✅ Implemented for context-aware subtitle generation
"""

# Standard library
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BiasWindow:
    """
    Time-based window for bias term injection during ASR.
    
    Attributes:
        start: Start time in seconds
        end: End time in seconds
        terms: List of bias terms to emphasize
        context: Optional context description
        confidence: Confidence score for these terms (0.0-1.0)
    """
    start: float
    end: float
    terms: List[str]
    context: Optional[str] = None
    confidence: float = 1.0
    
    def contains_time(self, time: float) -> bool:
        """Check if this window contains the given time."""
        return self.start <= time <= self.end
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def get_window_for_time(
    time: float,
    windows: Optional[List[BiasWindow]] = None
) -> Optional[BiasWindow]:
    """
    Get the bias window that contains the given time.
    
    Args:
        time: Time in seconds
        windows: List of bias windows
        
    Returns:
        BiasWindow if found, None otherwise
    """
    if not windows:
        return None
    
    for window in windows:
        if window.contains_time(time):
            return window
    
    return None


def create_bias_windows(
    glossary_terms: List[str],
    duration: float,
    window_size: float = 30.0,
    overlap: float = 5.0
) -> List[BiasWindow]:
    """
    Create overlapping bias windows from glossary terms.
    
    Args:
        glossary_terms: List of glossary terms to bias
        duration: Total audio duration in seconds
        window_size: Size of each window in seconds (default: 30s)
        overlap: Overlap between windows in seconds (default: 5s)
        
    Returns:
        List of BiasWindow objects with overlap
        
    Example:
        >>> terms = ["Aditi", "Jai", "Meow", "Mumbai"]
        >>> windows = create_bias_windows(terms, 120.0, window_size=30.0)
        >>> len(windows)
        5  # 120s / (30s - 5s overlap) = ~5 windows
    """
    if not glossary_terms or duration <= 0:
        return []
    
    windows = []
    current_time = 0.0
    step = window_size - overlap
    
    while current_time < duration:
        end_time = min(current_time + window_size, duration)
        
        windows.append(BiasWindow(
            start=current_time,
            end=end_time,
            terms=glossary_terms[:],  # Copy all terms to each window
            context=f"Window {len(windows) + 1}",
            confidence=1.0
        ))
        
        current_time += step
        
        # Prevent infinite loop
        if current_time >= duration:
            break
    
    logger.info(f"Created {len(windows)} bias windows for {duration:.1f}s audio")
    return windows


def create_dynamic_windows(
    glossary_dict: Dict[str, Dict[str, Any]],
    segment_times: List[Dict[str, float]],
    context: str = "dynamic"
) -> List[BiasWindow]:
    """
    Create dynamic bias windows based on segment timing.
    
    Useful for scene-based or speaker-based bias injection.
    
    Args:
        glossary_dict: Dictionary of terms with metadata
        segment_times: List of dicts with 'start' and 'end' times
        context: Context description for these windows
        
    Returns:
        List of BiasWindow objects matching segments
    """
    windows = []
    
    for i, segment in enumerate(segment_times):
        # Extract terms relevant to this segment
        # (Future enhancement: use context-aware term selection)
        terms = list(glossary_dict.keys())
        
        windows.append(BiasWindow(
            start=segment["start"],
            end=segment["end"],
            terms=terms,
            context=f"{context}_segment_{i}",
            confidence=segment.get("confidence", 1.0)
        ))
    
    return windows


def save_bias_windows(
    windows: List[BiasWindow],
    output_path: Path
) -> None:
    """
    Save bias windows to JSON file.
    
    Args:
        windows: List of bias windows
        output_path: Path to output JSON file
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "window_count": len(windows),
            "windows": [w.to_dict() for w in windows]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(windows)} bias windows to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save bias windows: {e}", exc_info=True)
        raise IOError(f"Cannot write bias windows to {output_path}: {e}")


def load_bias_windows(input_path: Path) -> List[BiasWindow]:
    """
    Load bias windows from JSON file.
    
    Args:
        input_path: Path to input JSON file
        
    Returns:
        List of BiasWindow objects
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If JSON format is invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Bias windows file not found: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Support both old and new format
        if isinstance(data, list):
            # Old format: direct list
            windows_data = data
        else:
            # New format: dict with metadata
            windows_data = data.get("windows", [])
        
        windows = [
            BiasWindow(
                start=w["start"],
                end=w["end"],
                terms=w["terms"],
                context=w.get("context"),
                confidence=w.get("confidence", 1.0)
            )
            for w in windows_data
        ]
        
        logger.info(f"Loaded {len(windows)} bias windows from {input_path}")
        return windows
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in bias windows file: {e}", exc_info=True)
        raise ValueError(f"Invalid bias windows JSON: {e}")
    except Exception as e:
        logger.error(f"Failed to load bias windows: {e}", exc_info=True)
        raise


def merge_windows(
    windows: List[BiasWindow],
    gap_threshold: float = 1.0
) -> List[BiasWindow]:
    """
    Merge adjacent windows if gap is below threshold.
    
    Args:
        windows: List of bias windows (must be sorted by start time)
        gap_threshold: Maximum gap in seconds to merge (default: 1.0s)
        
    Returns:
        List of merged BiasWindow objects
    """
    if not windows:
        return []
    
    # Sort by start time
    sorted_windows = sorted(windows, key=lambda w: w.start)
    
    merged = [sorted_windows[0]]
    
    for current in sorted_windows[1:]:
        last = merged[-1]
        
        # Check if gap is small enough to merge
        if current.start - last.end <= gap_threshold:
            # Merge: extend end time, combine terms
            last.end = current.end
            last.terms = list(set(last.terms + current.terms))  # Unique terms
            last.context = f"{last.context},{current.context}" if last.context and current.context else last.context or current.context
        else:
            merged.append(current)
    
    logger.info(f"Merged {len(windows)} windows into {len(merged)} windows")
    return merged


def filter_terms_by_frequency(
    terms: List[str],
    frequency_map: Dict[str, int],
    min_frequency: int = 2
) -> List[str]:
    """
    Filter bias terms by minimum frequency.
    
    Useful for removing rare terms that may cause false positives.
    
    Args:
        terms: List of candidate terms
        frequency_map: Dictionary mapping terms to their frequency
        min_frequency: Minimum frequency to include term
        
    Returns:
        Filtered list of terms
    """
    filtered = [
        term for term in terms
        if frequency_map.get(term, 0) >= min_frequency
    ]
    
    logger.debug(f"Filtered {len(terms)} terms to {len(filtered)} (min_freq={min_frequency})")
    return filtered
