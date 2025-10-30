#!/usr/bin/env python3
"""
Subtitle Generation container - Create .srt files

Workflow: Stage 9 (per workflow-arch.txt)
Input: post_ner/*.corrected.json
Output: en_merged/*.srt with speaker-prefixed subtitles
"""
import sys
import json
import os
from pathlib import Path
from typing import List, Dict

# Setup paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/shared')

from logger import PipelineLogger


def format_srt_time(seconds: float) -> str:
    """
    Format seconds as SRT timestamp (HH:MM:SS,mmm)
    
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


def merge_short_subtitles(
    segments: List[Dict],
    max_duration: float = 7.0,
    max_chars: int = 84
) -> List[Dict]:
    """
    Merge consecutive short subtitles from same speaker
    
    Args:
        segments: List of subtitle segments
        max_duration: Maximum duration for merged subtitle (seconds)
        max_chars: Maximum characters per subtitle
    
    Returns:
        Merged segments
    """
    if not segments:
        return []
    
    merged = []
    current = None
    
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        
        speaker = segment.get("speaker", "")
        start = segment.get("start", 0)
        end = segment.get("end", start + 1)
        
        if current is None:
            # Start new subtitle
            current = {
                "speaker": speaker,
                "start": start,
                "end": end,
                "text": text
            }
        elif (current["speaker"] == speaker and
              end - current["start"] <= max_duration and
              len(current["text"]) + len(text) + 1 <= max_chars):
            # Merge with current
            current["text"] += " " + text
            current["end"] = end
        else:
            # Save current and start new
            merged.append(current)
            current = {
                "speaker": speaker,
                "start": start,
                "end": end,
                "text": text
            }
    
    # Add final subtitle
    if current:
        merged.append(current)
    
    return merged


def generate_srt(
    segments: List[Dict],
    output_file: Path,
    include_speaker: bool = True,
    logger: PipelineLogger = None
):
    """
    Generate SRT subtitle file from segments
    
    Args:
        segments: List of subtitle segments
        output_file: Output SRT file path
        include_speaker: Include speaker labels in subtitles
        logger: Logger instance
    """
    if logger:
        logger.info(f"Generating SRT with {len(segments)} subtitles...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, 1):
            start = segment.get("start", 0)
            end = segment.get("end", start + 1)
            text = segment.get("text", "").strip()
            speaker = segment.get("speaker", "")
            
            if not text:
                continue
            
            # Format timestamps
            start_time = format_srt_time(start)
            end_time = format_srt_time(end)
            
            # Add speaker prefix if enabled
            if include_speaker and speaker:
                text = f"[{speaker}] {text}"
            
            # Write SRT entry
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n")
            f.write("\n")
    
    if logger:
        logger.info(f"✓ SRT file generated: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: subtitle_gen.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    # Setup logger
    logger = PipelineLogger("subtitle-gen")
    logger.info(f"Starting subtitle generation for: {movie_dir}")
    
    # Find corrected transcript (Post-NER output - preferred)
    corrected_files = list(movie_dir.glob("post_ner/*.corrected.json"))
    
    # Fallback to ASR if post-ner not available
    # (ASR already has speaker labels from diarization per workflow-arch.txt)
    if not corrected_files:
        logger.warning("No post-ner output found, using ASR transcript with speaker labels")
        corrected_files = list(movie_dir.glob("asr/*.asr.json"))
    
    if not corrected_files:
        logger.error("No transcript found")
        sys.exit(1)
    
    input_file = corrected_files[0]
    logger.info(f"Input transcript: {input_file}")
    
    # Load segments
    with open(input_file) as f:
        data = json.load(f)
    
    # Handle different formats
    if isinstance(data, dict):
        segments = data.get("segments", [])
    elif isinstance(data, list):
        segments = data
    else:
        logger.error("Unknown transcript format")
        sys.exit(1)
    
    logger.info(f"Loaded {len(segments)} segments")
    
    # Get config
    merge_subtitles = os.getenv("MERGE_SUBTITLES", "true").lower() == "true"
    include_speaker = os.getenv("INCLUDE_SPEAKER", "true").lower() == "true"
    max_duration = float(os.getenv("MAX_SUBTITLE_DURATION", "7.0"))
    max_chars = int(os.getenv("MAX_SUBTITLE_CHARS", "84"))
    
    logger.info(f"Merge subtitles: {merge_subtitles}")
    logger.info(f"Include speaker: {include_speaker}")
    
    # Merge if requested
    if merge_subtitles:
        logger.info("Merging consecutive short subtitles...")
        segments = merge_short_subtitles(
            segments,
            max_duration=max_duration,
            max_chars=max_chars
        )
        logger.info(f"After merging: {len(segments)} subtitles")
    
    # Setup output
    output_dir = movie_dir / "en_merged"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{movie_dir.name}.merged.srt"
    
    # Generate SRT
    try:
        generate_srt(
            segments,
            output_file,
            include_speaker=include_speaker,
            logger=logger
        )
        
        logger.info(f"✓ Subtitle generation complete")
        logger.info(f"Output: {output_file}")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
