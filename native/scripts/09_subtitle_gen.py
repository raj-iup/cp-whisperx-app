#!/usr/bin/env python3
"""Stage 9: Subtitle Generation (.srt format)"""
import sys
import json
import argparse
import os
from pathlib import Path

sys.path.insert(0, 'native/utils')
from native_logger import NativePipelineLogger
from manifest import StageManifest


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'subtitle_format': os.getenv('SUBTITLE_FORMAT', 'srt'),
        'max_line_length': int(os.getenv('SUBTITLE_MAX_LINE_LENGTH', '42')),
        'max_lines': int(os.getenv('SUBTITLE_MAX_LINES', '2')),
        'include_speaker': os.getenv('SUBTITLE_INCLUDE_SPEAKER_LABELS', 'true').lower() == 'true',
        'speaker_format': os.getenv('SUBTITLE_SPEAKER_FORMAT', '[{speaker}]'),
        'word_level': os.getenv('SUBTITLE_WORD_LEVEL_TIMESTAMPS', 'false').lower() == 'true',
        'max_duration': float(os.getenv('SUBTITLE_MAX_DURATION', '7.0')),
        'merge_short': os.getenv('SUBTITLE_MERGE_SHORT', 'true').lower() == 'true'
    }


def format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_speaker_label(speaker: str, speaker_format: str) -> str:
    """Format speaker label according to template."""
    if not speaker or not speaker_format:
        return ""
    return speaker_format.replace("{speaker}", speaker)


def split_long_lines(text: str, max_line_length: int, max_lines: int) -> str:
    """Split long text into multiple lines."""
    if len(text) <= max_line_length:
        return text
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        if current_length + word_length + (1 if current_line else 0) <= max_line_length:
            current_line.append(word)
            current_length += word_length + (1 if current_length > 0 else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length
            
            if len(lines) >= max_lines:
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines[:max_lines])


def merge_short_subtitles(segments: list, max_duration: float, max_chars: int) -> list:
    """Merge consecutive short subtitles from same speaker."""
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
            current = {
                "speaker": speaker,
                "start": start,
                "end": end,
                "text": text
            }
        elif (current["speaker"] == speaker and
              end - current["start"] <= max_duration and
              len(current["text"]) + len(text) + 1 <= max_chars):
            current["text"] += " " + text
            current["end"] = end
        else:
            merged.append(current)
            current = {
                "speaker": speaker,
                "start": start,
                "end": end,
                "text": text
            }
    
    if current:
        merged.append(current)
    
    return merged


def generate_srt(
    segments: list,
    config: dict,
    logger
) -> tuple:
    """
    Generate SRT content from segments.
    
    Args:
        segments: List of subtitle segments
        config: Configuration dict
        logger: Logger instance
        
    Returns:
        Tuple of (srt_content, statistics)
    """
    logger.info("Generating SRT subtitles")
    
    lines = []
    subtitle_count = 0
    total_duration = 0.0
    speakers = set()
    lyric_count = 0
    
    for i, segment in enumerate(segments, 1):
        start = segment.get("start", 0)
        end = segment.get("end", start + 1)
        text = segment.get("text", "").strip()
        speaker = segment.get("speaker", "")
        is_lyric = segment.get("is_lyric", False)
        
        if not text:
            continue
        
        subtitle_count += 1
        total_duration += (end - start)
        
        if speaker:
            speakers.add(speaker)
        
        if is_lyric:
            lyric_count += 1
        
        # Format timestamps
        start_time = format_srt_time(start)
        end_time = format_srt_time(end)
        
        # Format text based on content type
        if is_lyric:
            # Special formatting for lyrics
            text = f"♪ {text} ♪"
        elif config['include_speaker'] and speaker:
            # Add speaker prefix for dialogue
            speaker_label = format_speaker_label(speaker, config['speaker_format'])
            text = f"{speaker_label} {text}"
        
        # Split long lines
        text = split_long_lines(text, config['max_line_length'], config['max_lines'])
        
        # Build SRT entry
        lines.append(f"{subtitle_count}")
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text)
        lines.append("")  # Empty line between entries
    
    srt_content = "\n".join(lines)
    
    stats = {
        'original_segments': len(segments),
        'total_subtitles': subtitle_count,
        'total_duration': total_duration,
        'avg_subtitle_duration': total_duration / subtitle_count if subtitle_count > 0 else 0,
        'speakers': len(speakers),
        'lyric_subtitles': lyric_count
    }
    
    return srt_content, stats


def run_subtitle_generation(
    transcript_file: Path,
    logger,
    config: dict
):
    """
    Generate SRT subtitles from transcript.
    
    Args:
        transcript_file: Path to transcript JSON (corrected or original)
        logger: Logger instance
        config: Configuration dict
        
    Returns:
        Tuple of (srt_content, statistics)
    """
    logger.info(f"Configuration:")
    logger.info(f"  Format: {config['subtitle_format']}")
    logger.info(f"  Max line length: {config['max_line_length']}")
    logger.info(f"  Max lines: {config['max_lines']}")
    logger.info(f"  Include speaker: {config['include_speaker']}")
    logger.info(f"  Speaker format: {config['speaker_format']}")
    logger.info(f"  Word-level timestamps: {config['word_level']}")
    logger.info(f"  Max duration: {config['max_duration']}s")
    logger.info(f"  Merge short subtitles: {config['merge_short']}")
    
    # Load transcript
    if not transcript_file.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    # Extract segments
    if isinstance(transcript_data, dict):
        segments = transcript_data.get('segments', [])
    elif isinstance(transcript_data, list):
        segments = transcript_data
    else:
        raise ValueError("Unknown transcript format")
    
    logger.info(f"Loaded {len(segments)} segments")
    
    if config['word_level']:
        logger.warning("Word-level timestamps requested but not yet implemented")
    
    import time
    start = time.time()
    
    # Merge if requested
    if config['merge_short']:
        logger.info("Merging consecutive short subtitles...")
        max_chars = config['max_line_length'] * config['max_lines']
        segments = merge_short_subtitles(
            segments,
            config['max_duration'],
            max_chars
        )
        logger.info(f"After merging: {len(segments)} subtitles")
    
    # Generate SRT
    srt_content, stats = generate_srt(segments, config, logger)
    
    duration = time.time() - start
    
    # Log results
    logger.log_processing("Subtitle generation complete", duration)
    logger.log_metric("Original segments", stats['original_segments'])
    logger.log_metric("Total subtitles", stats['total_subtitles'])
    logger.log_metric("Total duration", f"{stats['total_duration']:.2f}s")
    logger.log_metric("Avg subtitle duration", f"{stats['avg_subtitle_duration']:.2f}s")
    logger.log_metric("Unique speakers", stats['speakers'])
    
    return srt_content, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('subtitle_gen', movie_name)
    
    try:
        logger.log_stage_start("Subtitle Generation - SRT format")
        
        # Load configuration from environment
        env_config = load_env_config()
        
        logger.info(f"Configuration loaded from environment")
        
        import time
        start = time.time()
        
        with StageManifest('subtitle_gen', movie_dir, logger.logger) as manifest:
            # Find transcript - prefer corrected, fallback to ASR
            corrected_files = list(movie_dir.glob('post_ner/*.corrected.json'))
            
            if not corrected_files:
                logger.warning("No post-NER output found, using ASR transcript")
                corrected_files = list(movie_dir.glob('asr/*.asr.json'))
            
            if not corrected_files:
                raise FileNotFoundError("No transcript found")
            
            transcript_file = corrected_files[0]
            logger.debug(f"Transcript file: {transcript_file}")
            
            # Run subtitle generation with configuration
            srt_content, stats = run_subtitle_generation(
                transcript_file=transcript_file,
                logger=logger,
                config=env_config
            )
            
            duration = time.time() - start
            
            # Create output directory
            subtitle_dir = movie_dir / 'en_merged'
            subtitle_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Subtitle directory: {subtitle_dir}")
            
            # Save subtitle file
            subtitle_format = env_config['subtitle_format']
            output_file = subtitle_dir / f'{movie_name}.merged.{subtitle_format}'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.log_file_operation("Saved subtitle file", output_file, success=True)
            
            # Add to manifest
            manifest.add_output('subtitles', output_file, f'{subtitle_format.upper()} subtitle file')
            manifest.add_metadata('format', subtitle_format)
            manifest.add_metadata('subtitles', stats['total_subtitles'])
            manifest.add_metadata('speakers', stats['speakers'])
            manifest.add_metadata('include_speaker', env_config['include_speaker'])
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
