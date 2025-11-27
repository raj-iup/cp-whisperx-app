#!/usr/bin/env python3
"""
Subtitle Generation stage: Generate subtitle files from transcript
"""
import sys
import os
import json
from pathlib import Path
from datetime import timedelta, datetime

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

# Try to import glossary
try:
    from shared.glossary_unified import load_glossary
    GLOSSARY_AVAILABLE = True
except ImportError:
    GLOSSARY_AVAILABLE = False

def format_timestamp(seconds):
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_subtitle_text(segment, has_lyrics_data=False):
    """
    Format subtitle text based on lyrics detection
    
    Args:
        segment: Transcript segment
        has_lyrics_data: Whether lyrics detection data is available
    
    Returns:
        Formatted text string
    """
    text = segment.get('text', '').strip()
    
    if not text:
        return None
    
    # If no lyrics data, return plain text
    if not has_lyrics_data:
        return text
    
    # Check if this segment is lyrics
    is_lyrics = segment.get('is_lyrics', False)
    
    if is_lyrics:
        # Add musical notes around lyrics
        formatted_text = f"♪ {text} ♪"
        
        # Italicize lyrics
        formatted_text = f"<i>{formatted_text}</i>"
        
        # Add song metadata if available (only for segments with song info)
        song_title = segment.get('song_title')
        song_artist = segment.get('song_artist')
        
        if song_title:
            # Add song metadata on separate line
            metadata = f'<i>Song: "{song_title}"'
            if song_artist:
                metadata += f" - {song_artist}"
            metadata += "</i>"
            
            # Only show metadata once per song (check if this is first segment of song)
            # We'll add metadata to first lyric segment with song info
            formatted_text = metadata + "\n" + formatted_text
    else:
        # Regular dialogue - no formatting
        formatted_text = text
    
    return formatted_text

def main():
    # Initialize StageIO
    stage_io = StageIO("subtitle_generation")
    
    # Setup logger
    logger = get_stage_logger("subtitle_generation", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("SUBTITLE GENERATION STAGE")
    logger.info("=" * 60)
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Load glossary if available and enabled
    glossary = None
    
    if GLOSSARY_AVAILABLE:
        try:
            glossary_enabled = getattr(config, 'glossary_enabled', True)
            
            if glossary_enabled:
                glossary_path = PROJECT_ROOT / getattr(config, 'glossary_path', 'glossary/unified_glossary.tsv')
                
                if glossary_path.exists():
                    film_title = getattr(config, 'film_title', '')
                    film_year = getattr(config, 'film_year', '')
                    film_name = f"{film_title}_{film_year}" if film_title and film_year else None
                    
                    glossary = load_glossary(glossary_path, film_name, logger)
                    
                    if glossary:
                        stats = glossary.get_statistics()
                        term_count = stats.get('total_terms', 0)
                        logger.info(f"✓ Loaded glossary: {term_count} terms")
                        
                        if term_count == 0:
                            logger.warning("Glossary loaded but contains 0 terms")
                            glossary = None
                    else:
                        logger.warning("Glossary object is None after loading")
                else:
                    logger.warning(f"Glossary not found: {glossary_path}")
        except Exception as e:
            logger.warning(f"Failed to load glossary: {e}")
    
    if glossary is None:
        logger.info("Glossary not loaded (disabled or unavailable)")
    
    # Try to read from lyrics detection (includes song metadata)
    # Fall back to ASR if lyrics detection not available
    transcript_file = stage_io.get_input_path("segments.json", from_stage="lyrics_detection")
    
    if not transcript_file.exists():
        logger.info("Lyrics detection output not found, falling back to ASR")
        transcript_file = stage_io.get_input_path("transcript.json", from_stage="asr")
        has_lyrics_data = False
    else:
        logger.info("Using lyrics detection output (includes song metadata)")
        has_lyrics_data = True
    
    if not transcript_file.exists():
        logger.error(f"Transcript not found: {transcript_file}")
        return 1
    
    logger.info(f"Reading transcript from: {transcript_file}")
    
    with open(transcript_file, 'r', encoding='utf-8', errors='replace') as f:
        transcript = json.load(f)
    
    # Generate SRT file using StageIO
    srt_file = stage_io.get_output_path("subtitles.srt")
    
    logger.info(f"Generating subtitles: {srt_file}")
    if has_lyrics_data:
        logger.info("Enhanced mode: Including song metadata and lyrics formatting")
    
    subtitle_count = 0
    lyrics_count = 0
    last_song_title = None  # Track last song to avoid duplicate metadata
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        if isinstance(transcript, dict) and 'segments' in transcript:
            for i, segment in enumerate(transcript['segments'], 1):
                start = segment.get('start', 0)
                end = segment.get('end', start + 1)
                
                # Check if this is a new song (to show metadata only once)
                current_song = segment.get('song_title')
                if current_song and current_song != last_song_title:
                    # This is the first segment of a new song
                    last_song_title = current_song
                else:
                    # Not a new song, remove song_title to avoid duplicate metadata
                    if 'song_title' in segment:
                        # Create a copy without song metadata for formatting
                        segment = segment.copy()
                        segment.pop('song_title', None)
                        segment.pop('song_artist', None)
                
                # Format the text
                formatted_text = format_subtitle_text(segment, has_lyrics_data)
                
                # Apply glossary if available (only to dialogue, not lyrics metadata)
                if formatted_text and glossary and not segment.get('is_lyrics'):
                    formatted_text = glossary.apply(formatted_text)
                
                if formatted_text:
                    f.write(f"{i}\n")
                    f.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
                    f.write(f"{formatted_text}\n\n")
                    subtitle_count += 1
                    
                    if segment.get('is_lyrics'):
                        lyrics_count += 1
    
    # Save metadata
    metadata = {
        "status": "completed",
        "subtitle_count": subtitle_count,
        "lyrics_count": lyrics_count if has_lyrics_data else 0,
        "has_lyrics_formatting": has_lyrics_data,
        "format": "srt",
        "subtitle_file": str(srt_file)
    }
    stage_io.save_metadata(metadata)
    
    logger.info(f"✓ Subtitles generated successfully")
    logger.info(f"  Subtitle count: {subtitle_count}")
    if has_lyrics_data:
        logger.info(f"  Lyrics subtitles: {lyrics_count}")
        logger.info(f"  Dialogue subtitles: {subtitle_count - lyrics_count}")
    logger.info(f"  Output file: {srt_file}")
    
    # Update manifest
    manifest_file = output_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8', errors='replace') as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    manifest.setdefault('stages', {})['subtitle_gen'] = {
        'status': 'completed',
        'subtitle_file': str(srt_file)
    }
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
