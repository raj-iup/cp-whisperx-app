"""
Media identity computation for caching system.

Per AD-014: Compute stable identifiers from audio content that persist
across file renames, re-encoding, and metadata changes.

Architecture Decision: AD-014 (Multi-Phase Subtitle Workflow)
"""
from pathlib import Path
import hashlib
import subprocess
import json
from typing import Optional
import tempfile


def compute_media_id(media_path: Path, sample_duration: int = 30) -> str:
    """
    Compute stable identifier from audio content.
    
    Uses SHA256 hash of audio samples extracted at multiple points in the media.
    This ensures the same audio content produces the same ID regardless of:
    - Filename changes
    - Video re-encoding
    - Metadata modifications
    - Container format changes
    
    Args:
        media_path: Path to media file (video or audio)
        sample_duration: Duration of each sample in seconds (default: 30)
        
    Returns:
        SHA256 hash string (64 hex characters)
        
    Raises:
        FileNotFoundError: If media file doesn't exist
        RuntimeError: If FFmpeg extraction fails
        
    Example:
        >>> media_id = compute_media_id(Path("movie.mp4"))
        >>> print(media_id)
        'a1b2c3d4e5f6...'  # 64-character hash
        
    Note:
        - Samples from beginning, middle, and end of media
        - Uses raw PCM audio data (format-independent)
        - Cached results valid indefinitely for same content
    """
    media_path = Path(media_path).resolve()
    
    # Validation
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found: {media_path}")
    
    if not media_path.is_file():
        raise RuntimeError(f"Path is not a file: {media_path}")
    
    # Get media duration
    duration = _get_media_duration(media_path)
    
    if duration is None or duration < sample_duration:
        # For short media, hash the entire audio
        return _hash_audio_segment(media_path, start=0, duration=None)
    
    # Sample at 3 points: beginning, middle, end
    sample_points = [
        0,  # Beginning
        duration / 2 - sample_duration / 2,  # Middle
        duration - sample_duration  # End
    ]
    
    # Extract and hash samples
    sample_hashes = []
    for start_time in sample_points:
        segment_hash = _hash_audio_segment(
            media_path,
            start=start_time,
            duration=sample_duration
        )
        sample_hashes.append(segment_hash)
    
    # Combine sample hashes into final media ID
    combined = ''.join(sample_hashes)
    final_hash = hashlib.sha256(combined.encode()).hexdigest()
    
    return final_hash


def _get_media_duration(media_path: Path) -> Optional[float]:
    """
    Get media duration in seconds using FFprobe.
    
    Args:
        media_path: Path to media file
        
    Returns:
        Duration in seconds, or None if cannot determine
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        str(media_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        data = json.loads(result.stdout)
        duration_str = data.get('format', {}).get('duration')
        
        if duration_str:
            return float(duration_str)
        return None
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
        return None


def _hash_audio_segment(
    media_path: Path,
    start: float,
    duration: Optional[float]
) -> str:
    """
    Extract audio segment and compute SHA256 hash.
    
    Args:
        media_path: Path to media file
        start: Start time in seconds
        duration: Duration in seconds, or None for entire file
        
    Returns:
        SHA256 hash of raw PCM audio data
        
    Raises:
        RuntimeError: If FFmpeg extraction fails
    """
    # Build FFmpeg command to extract raw PCM audio
    cmd = ['ffmpeg', '-y']
    
    # Seek to start position (fast seek before input)
    if start > 0:
        cmd.extend(['-ss', str(start)])
    
    # Input file
    cmd.extend(['-i', str(media_path)])
    
    # Duration limit
    if duration is not None:
        cmd.extend(['-t', str(duration)])
    
    # Output format: raw PCM, 16kHz, mono, 16-bit
    # This format is:
    # - Format-independent (works for any input)
    # - Deterministic (same audio = same bytes)
    # - Efficient (lower sample rate for hashing)
    cmd.extend([
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # 16-bit PCM
        '-ar', '16000',  # 16kHz (good enough for fingerprinting)
        '-ac', '1',  # Mono
        '-f', 's16le',  # Raw PCM format
        'pipe:1'  # Output to stdout
    ])
    
    try:
        # Run FFmpeg and capture audio data
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            timeout=60
        )
        
        # Hash the raw audio bytes
        audio_data = result.stdout
        hash_obj = hashlib.sha256(audio_data)
        return hash_obj.hexdigest()
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FFmpeg audio extraction failed: {e.stderr.decode() if e.stderr else str(e)}"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg audio extraction timed out")


def compute_glossary_hash(glossary_path: Path) -> str:
    """
    Compute hash of glossary file for cache invalidation.
    
    Args:
        glossary_path: Path to glossary JSON file
        
    Returns:
        SHA256 hash of glossary content
        
    Example:
        >>> hash1 = compute_glossary_hash(Path("glossary.json"))
        >>> # Modify glossary
        >>> hash2 = compute_glossary_hash(Path("glossary.json"))
        >>> assert hash1 != hash2  # Different hashes after modification
    """
    glossary_path = Path(glossary_path).resolve()
    
    if not glossary_path.exists():
        # Empty glossary (no file)
        return hashlib.sha256(b'').hexdigest()
    
    # Read and hash file content
    with open(glossary_path, 'rb') as f:
        content = f.read()
    
    return hashlib.sha256(content).hexdigest()


def verify_media_id_stability(media_path: Path, iterations: int = 3) -> bool:
    """
    Verify that media_id computation is stable across multiple runs.
    
    Args:
        media_path: Path to media file
        iterations: Number of times to compute ID
        
    Returns:
        True if all IDs match, False otherwise
        
    Example:
        >>> assert verify_media_id_stability(Path("movie.mp4"))
    """
    ids = [compute_media_id(media_path) for _ in range(iterations)]
    return len(set(ids)) == 1  # All IDs should be identical
