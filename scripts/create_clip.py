#!/usr/bin/env python3
"""
Create video clip with soft-embedded subtitles for transcribe mode.
Extracts specified time window and adds subtitle track (can be toggled on/off).
"""
import sys
import os
import subprocess
from pathlib import Path
import json

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config


def format_time_for_ffmpeg(time_str: str) -> str:
    """
    Convert time format to ffmpeg format.
    Handles both HH:MM:SS and seconds formats.
    """
    if ':' in time_str:
        return time_str
    else:
        # Convert seconds to HH:MM:SS
        seconds = float(time_str)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_video_duration(video_path: Path, logger) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get video duration: {e}")
        return 0


def create_clip_with_subtitles(
    input_video: Path,
    subtitle_file: Path,
    output_file: Path,
    start_time: str = None,
    end_time: str = None,
    subtitle_language: str = 'eng',
    subtitle_title: str = 'English',
    logger = None
) -> bool:
    """
    Create a video clip with soft-embedded subtitles (subtitle track).
    
    Args:
        input_video: Source video file
        subtitle_file: SRT subtitle file
        output_file: Output video file
        start_time: Start time (HH:MM:SS or seconds)
        end_time: End time (HH:MM:SS or seconds)
        subtitle_language: ISO 639-2 language code for subtitle track (e.g., 'eng', 'hin')
        subtitle_title: Human-readable title for subtitle track
        logger: Logger instance
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Creating video clip with soft-embedded subtitles...")
    logger.info(f"  Input: {input_video}")
    logger.info(f"  Subtitles: {subtitle_file}")
    logger.info(f"  Output: {output_file}")
    logger.info(f"  Subtitle language: {subtitle_language} ({subtitle_title})")
    
    # Prepare ffmpeg command
    cmd = ['ffmpeg', '-y']
    
    # Add time range if specified
    if start_time:
        start_ffmpeg = format_time_for_ffmpeg(start_time)
        cmd.extend(['-ss', start_ffmpeg])
        logger.info(f"  Start time: {start_ffmpeg}")
    
    if end_time:
        end_ffmpeg = format_time_for_ffmpeg(end_time)
        cmd.extend(['-to', end_ffmpeg])
        logger.info(f"  End time: {end_ffmpeg}")
    
    # Input video
    cmd.extend(['-i', str(input_video)])
    
    # Input subtitle file (as a second input stream)
    cmd.extend(['-i', str(subtitle_file)])
    
    # Map video and audio from first input, subtitle from second input
    cmd.extend([
        '-map', '0:v',              # Video from first input
        '-map', '0:a',              # Audio from first input
        '-map', '1:s',              # Subtitles from second input
        '-c:v', 'libx264',          # H.264 video codec
        '-preset', 'medium',         # Encoding speed/quality balance
        '-crf', '23',                # Quality (18-28, lower is better)
        '-c:a', 'aac',               # AAC audio codec
        '-b:a', '192k',              # Audio bitrate
        '-c:s', 'mov_text',          # Subtitle codec for MP4 (soft subtitles)
        '-metadata:s:s:0', f'language={subtitle_language}',  # Mark subtitle track with correct language
        '-metadata:s:s:0', f'title={subtitle_title}',        # Subtitle track title
        '-disposition:s:0', 'default',       # Make subtitle track default
        '-movflags', '+faststart',   # Web-optimized
        str(output_file)
    ])
    
    logger.info("Running ffmpeg (soft subtitles mode)...")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stderr and 'error' not in result.stderr.lower():
            logger.debug(f"FFmpeg output: {result.stderr[-500:]}")  # Last 500 chars
        
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Video clip created: {output_file.name} ({file_size_mb:.1f} MB)")
            logger.info(f"  Subtitle track: Soft-embedded (can be toggled on/off)")
            return True
        else:
            logger.error("FFmpeg completed but output file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def create_clip_with_multiple_subtitles(
    input_video: Path,
    subtitle_files: list,
    output_file: Path,
    start_time: str = None,
    end_time: str = None,
    logger = None
) -> bool:
    """
    Create a video clip with multiple soft-embedded subtitle tracks.
    
    Args:
        input_video: Source video file
        subtitle_files: List of tuples (subtitle_file_path, language_code, title)
        output_file: Output video file
        start_time: Start time (HH:MM:SS or seconds)
        end_time: End time (HH:MM:SS or seconds)
        logger: Logger instance
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Creating video clip with multiple soft-embedded subtitle tracks...")
    logger.info(f"  Input: {input_video}")
    logger.info(f"  Output: {output_file}")
    logger.info(f"  Subtitle tracks: {len(subtitle_files)}")
    for i, (_, lang_code, title) in enumerate(subtitle_files):
        logger.info(f"    Track {i+1}: {title} ({lang_code})")
    
    # Prepare ffmpeg command
    cmd = ['ffmpeg', '-y']
    
    # Add time range if specified
    if start_time:
        start_ffmpeg = format_time_for_ffmpeg(start_time)
        cmd.extend(['-ss', start_ffmpeg])
        logger.info(f"  Start time: {start_ffmpeg}")
    
    if end_time:
        end_ffmpeg = format_time_for_ffmpeg(end_time)
        cmd.extend(['-to', end_ffmpeg])
        logger.info(f"  End time: {end_ffmpeg}")
    
    # Input video (input 0)
    cmd.extend(['-i', str(input_video)])
    
    # Input subtitle files (inputs 1, 2, 3, ...)
    for sub_file, _, _ in subtitle_files:
        cmd.extend(['-i', str(sub_file)])
    
    # Map video and audio from first input
    cmd.extend([
        '-map', '0:v',              # Video from first input
        '-map', '0:a',              # Audio from first input
    ])
    
    # Map each subtitle track
    for i in range(len(subtitle_files)):
        cmd.extend(['-map', f'{i+1}:s'])  # Subtitle from input i+1
    
    # Video and audio encoding options
    cmd.extend([
        '-c:v', 'libx264',          # H.264 video codec
        '-preset', 'medium',         # Encoding speed/quality balance
        '-crf', '23',                # Quality (18-28, lower is better)
        '-c:a', 'aac',               # AAC audio codec
        '-b:a', '192k',              # Audio bitrate
        '-c:s', 'mov_text',          # Subtitle codec for MP4 (soft subtitles)
    ])
    
    # Add metadata for each subtitle track
    for i, (_, lang_code, title) in enumerate(subtitle_files):
        cmd.extend([
            '-metadata:s:s:' + str(i), f'language={lang_code}',
            '-metadata:s:s:' + str(i), f'title={title}',
        ])
        # Make first subtitle track default
        if i == 0:
            cmd.extend(['-disposition:s:' + str(i), 'default'])
        else:
            cmd.extend(['-disposition:s:' + str(i), '0'])
    
    # Web-optimized
    cmd.extend(['-movflags', '+faststart', str(output_file)])
    
    logger.info("Running ffmpeg (multiple subtitle tracks mode)...")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stderr and 'error' not in result.stderr.lower():
            logger.debug(f"FFmpeg output: {result.stderr[-500:]}")  # Last 500 chars
        
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Video clip created: {output_file.name} ({file_size_mb:.1f} MB)")
            logger.info(f"  Subtitle tracks: {len(subtitle_files)} soft-embedded (can be toggled)")
            return True
        else:
            logger.error("FFmpeg completed but output file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def main():
    """Main entry point for create_clip stage."""
    # Setup stage I/O and logging
    stage_io = StageIO("create_clip")
    logger = get_stage_logger("create_clip", log_level="INFO", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("CREATE_CLIP STAGE: Video Clip with Embedded Subtitles")
    logger.info("=" * 60)
    
    # Load configuration
    config_path_env = os.environ.get('CONFIG_PATH')
    if not config_path_env:
        logger.error("CONFIG_PATH environment variable not set")
        return 1
    
    logger.debug(f"Loading configuration from: {config_path_env}")
    config = load_config(config_path_env)
    
    # Get source video path
    # For clipped videos, IN_ROOT points to the clip in output dir
    # We want the ORIGINAL source file from job.json
    job_dir = Path(config_path_env).parent
    job_json = job_dir / "job.json"
    
    source_media = None
    clip_start = None
    clip_end = None
    job_data = {}
    
    if job_json.exists():
        import json
        with open(job_json, 'r') as f:
            job_data = json.load(f)
            source_media = job_data.get('source_media')
            clip_start = job_data.get('clip_start')
            clip_end = job_data.get('clip_end')
            logger.debug(f"Found source_media from job.json: {source_media}")
            if clip_start or clip_end:
                logger.debug(f"Clip time range: {clip_start} → {clip_end}")
    
    # Fallback to IN_ROOT if job.json not found
    if not source_media:
        source_media = getattr(config, 'in_root', None)
        logger.debug(f"Using in_root from config: {source_media}")
        # Try config for clip times as fallback
        clip_start = getattr(config, 'clip_start', None)
        clip_end = getattr(config, 'clip_end', None)
    
    # Fallback to IN_ROOT if job.json not found
    if not source_media:
        source_media = getattr(config, 'in_root', None)
        logger.debug(f"Using in_root from config: {source_media}")
    
    if not source_media:
        logger.error("Source media not found in configuration")
        logger.error("  Tried: job.json->source_media, config.in_root")
        return 1
    
    source_media = Path(source_media)
    if not source_media.exists():
        logger.error(f"Source video not found: {source_media}")
        return 1
    
    logger.info(f"Source video: {source_media}")
    
    # Get subtitle files from ASR stage
    job_id = getattr(config, 'job_id', 'output')
    
    # Try to find subtitle file with language suffix first
    target_lang = getattr(config, 'target_language', None)
    source_lang = getattr(config, 'source_language', 'hi')
    
    # Language name mapping
    lang_names = {
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
        'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
        'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
        'ta': 'Tamil', 'te': 'Telugu', 'bn': 'Bengali', 'ur': 'Urdu'
    }
    
    # ISO 639-2 language codes for subtitle metadata
    lang_codes_iso639_2 = {
        'en': 'eng', 'es': 'spa', 'fr': 'fra', 'de': 'deu',
        'it': 'ita', 'pt': 'por', 'ru': 'rus', 'ja': 'jpn',
        'ko': 'kor', 'zh': 'chi', 'ar': 'ara', 'hi': 'hin',
        'ta': 'tam', 'te': 'tel', 'bn': 'ben', 'ur': 'urd'
    }
    
    asr_dir = job_dir / "06_asr"
    workflow_mode = job_data.get('workflow_mode', 'transcribe')
    
    # Collect all available subtitle files
    subtitle_tracks = []
    
    # Always look for source language subtitle first
    source_subtitle = asr_dir / f"{job_id}.srt"
    if source_subtitle.exists():
        source_lang_name = lang_names.get(source_lang, source_lang.upper())
        source_lang_code = lang_codes_iso639_2.get(source_lang, 'und')
        subtitle_tracks.append((source_subtitle, source_lang_code, source_lang_name))
        logger.info(f"Found source language subtitle: {source_subtitle.name} ({source_lang_name})")
    
    # Look for target language subtitle if specified
    if target_lang and target_lang != 'auto' and target_lang != source_lang:
        target_lang_name = lang_names.get(target_lang, target_lang.upper())
        target_subtitle = asr_dir / f"{job_id}-{target_lang_name}.srt"
        if target_subtitle.exists():
            target_lang_code = lang_codes_iso639_2.get(target_lang, 'und')
            subtitle_tracks.append((target_subtitle, target_lang_code, target_lang_name))
            logger.info(f"Found target language subtitle: {target_subtitle.name} ({target_lang_name})")
    
    if not subtitle_tracks:
        logger.error(f"No subtitle files found in ASR directory: {asr_dir}")
        logger.error(f"  Tried: {job_id}.srt, {job_id}-*.srt")
        return 1
    
    logger.info(f"Total subtitle tracks to embed: {len(subtitle_tracks)}")
    
    # Use time range from job.json (already loaded above)
    start_time = clip_start
    end_time = clip_end
    
    if start_time or end_time:
        logger.info(f"Time range: {start_time or '00:00:00'} → {end_time or 'end'}")
    else:
        logger.info("Processing full video")
    
    # Determine output filename
    source_stem = source_media.stem
    output_file = stage_io.stage_dir / f"{source_stem}_subtitled.mp4"
    
    # Create clip with subtitles (single or multiple tracks)
    if len(subtitle_tracks) == 1:
        # Single subtitle track - use simple method
        subtitle_file, subtitle_lang_code, subtitle_lang_name = subtitle_tracks[0]
        success = create_clip_with_subtitles(
            input_video=source_media,
            subtitle_file=subtitle_file,
            output_file=output_file,
            start_time=start_time,
            end_time=end_time,
            subtitle_language=subtitle_lang_code,
            subtitle_title=subtitle_lang_name,
            logger=logger
        )
    else:
        # Multiple subtitle tracks - use advanced method
        success = create_clip_with_multiple_subtitles(
            input_video=source_media,
            subtitle_files=subtitle_tracks,
            output_file=output_file,
            start_time=start_time,
            end_time=end_time,
            logger=logger
        )
    
    if success:
        logger.info("=" * 60)
        logger.info("CREATE_CLIP STAGE COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Output: {output_file}")
        return 0
    else:
        logger.error("Failed to create video clip")
        return 1


if __name__ == "__main__":
    sys.exit(main())
