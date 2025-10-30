"""
bias_injection.py - Rolling windowed prompt injection for WhisperX

Creates compact bias prompts for each rolling window to stabilize
proper nouns within scene context.
"""

import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class BiasWindow:
    """A single bias window"""
    window_id: int
    start_time: float
    end_time: float
    bias_terms: List[str]
    bias_prompt: str


def create_bias_windows(
    duration_seconds: float,
    window_seconds: int,
    stride_seconds: int,
    base_terms: List[str],
    topk: int = 10,
    decay: float = 0.9
) -> List[BiasWindow]:
    """
    Create rolling bias windows for the video

    Args:
        duration_seconds: Total video duration
        window_seconds: Window size (e.g., 45s)
        stride_seconds: Stride between windows (e.g., 15s)
        base_terms: Base list of terms (names, places) from era/TMDB
        topk: Number of top terms to include per window
        decay: Decay factor for term weighting (future use)

    Returns:
        List of BiasWindow objects
    """
    windows = []
    window_id = 0
    start_time = 0.0

    while start_time < duration_seconds:
        end_time = min(start_time + window_seconds, duration_seconds)

        # For now, use top-k terms uniformly
        # In future: implement dynamic weighting based on recent mentions
        bias_terms = base_terms[:topk]

        # Create compact bias prompt
        bias_prompt = ", ".join(bias_terms)

        windows.append(BiasWindow(
            window_id=window_id,
            start_time=start_time,
            end_time=end_time,
            bias_terms=bias_terms,
            bias_prompt=bias_prompt
        ))

        window_id += 1
        start_time += stride_seconds

    return windows


def save_bias_windows(
    bias_dir: Path,
    windows: List[BiasWindow],
    basename: str
):
    """
    Save bias windows to JSON files

    Args:
        bias_dir: Directory to save bias windows
        windows: List of BiasWindow objects
        basename: Base filename for output
    """
    bias_dir.mkdir(parents=True, exist_ok=True)

    # Save each window as separate JSON
    for window in windows:
        window_file = bias_dir / f"{basename}.bias.window.{window.window_id:04d}.json"

        window_data = {
            "window_id": window.window_id,
            "start_time": window.start_time,
            "end_time": window.end_time,
            "bias_terms": window.bias_terms,
            "bias_prompt": window.bias_prompt
        }

        with open(window_file, "w") as f:
            json.dump(window_data, f, indent=2)

    # Also save summary of all windows
    summary_file = bias_dir / f"{basename}.bias.summary.json"
    summary_data = {
        "total_windows": len(windows),
        "windows": [
            {
                "window_id": w.window_id,
                "start_time": w.start_time,
                "end_time": w.end_time,
                "num_terms": len(w.bias_terms)
            }
            for w in windows
        ]
    }

    with open(summary_file, "w") as f:
        json.dump(summary_data, f, indent=2)


def get_window_for_time(windows: List[BiasWindow], time_seconds: float) -> BiasWindow:
    """
    Get bias window for a specific timestamp

    Args:
        windows: List of BiasWindow objects
        time_seconds: Timestamp in seconds

    Returns:
        Closest BiasWindow
    """
    for window in windows:
        if window.start_time <= time_seconds < window.end_time:
            return window

    # Fallback to last window if time exceeds all windows
    return windows[-1] if windows else None
