#!/usr/bin/env python3
"""
FFmpeg Mux Step
Embeds subtitle file into video as soft subtitles.
Outputs to: out/{movie}/
"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, '/app/shared')
from config import load_config
from logger import setup_logger
from utils import save_json, get_movie_dir


def mux_subtitles(video_file: Path, subtitle_file: Path, output_file: Path, config) -> bool:
    """
    Embed subtitles into video using FFmpeg.
    
    Args:
        video_file: Path to input video
        subtitle_file: Path to SRT subtitle file
        output_file: Path to output video with subtitles
        config: Pipeline configuration
    
    Returns:
        True if successful, False otherwise
    """
    logger = setup_logger(
        "mux",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    logger.info(f"Starting video muxing with subtitles")
    logger.info(f"Video: {video_file.name}")
    logger.info(f"Subtitles: {subtitle_file.name}")
    logger.info(f"Output: {output_file}")
    
    # Log config source
    import os
    config_path = os.getenv('CONFIG_PATH', '/app/config/.env')
    logger.info(f"Using config: {config_path}")
    
    # Get configuration parameters with detailed logging
    subtitle_codec = config.get("mux_subtitle_codec", "mov_text")
    subtitle_language = config.get("mux_subtitle_language", "eng")
    subtitle_title = config.get("mux_subtitle_title", "English")
    copy_video = config.get("mux_copy_video", True)
    copy_audio = config.get("mux_copy_audio", True)
    container_format = config.get("mux_container_format", "mp4")
    
    logger.info(f"Configuration:")
    logger.info(f"  Subtitle codec: {subtitle_codec} (from MUX_SUBTITLE_CODEC)")
    logger.info(f"  Subtitle language: {subtitle_language} (from MUX_SUBTITLE_LANGUAGE)")
    logger.info(f"  Subtitle title: {subtitle_title}")
    logger.info(f"  Copy video: {copy_video} (faster, no re-encoding)")
    logger.info(f"  Copy audio: {copy_audio} (faster, no re-encoding)")
    logger.info(f"  Container format: {container_format}")
    
    # Determine video codec
    if copy_video:
        video_codec = "copy"
    else:
        # Default to libx264 if re-encoding
        video_codec = "libx264"
        logger.info(f"Video will be re-encoded with {video_codec}")
    
    # Determine audio codec
    if copy_audio:
        audio_codec = "copy"
    else:
        # Default to aac if re-encoding
        audio_codec = "aac"
        logger.info(f"Audio will be re-encoded with {audio_codec}")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-i", str(subtitle_file),
            "-c:v", video_codec,
            "-c:a", audio_codec,
            "-c:s", subtitle_codec,
            "-metadata:s:s:0", f"language={subtitle_language}",
            "-metadata:s:s:0", f"title={subtitle_title}",
        ]
        
        # Add format-specific options
        if container_format.lower() == "mp4":
            cmd.extend(["-movflags", "+faststart"])
        
        cmd.append(str(output_file))
        
        logger.debug(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"[OK] Mux completed successfully")
        output_size = output_file.stat().st_size / (1024*1024)
        input_size = video_file.stat().st_size / (1024*1024)
        logger.info(f"[OK] Output size: {output_size:.2f} MB")
        logger.info(f"[OK] Input size: {input_size:.2f} MB")
        logger.info(f"[OK] Size difference: {output_size - input_size:+.2f} MB")
        
        # Save metadata
        metadata = {
            "video_file": str(video_file),
            "subtitle_file": str(subtitle_file),
            "output_file": str(output_file),
            "subtitle_codec": subtitle_codec,
            "subtitle_language": subtitle_language,
            "subtitle_title": subtitle_title,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "container_format": container_format,
            "copy_video": copy_video,
            "copy_audio": copy_audio,
            "file_size_mb": output_file.stat().st_size / (1024*1024)
        }
        
        metadata_file = output_file.parent / f"{output_file.stem}_mux_metadata.json"
        save_json(metadata, metadata_file)
        logger.info(f"Metadata saved: {metadata_file}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Mux failed: {e}")
        return False


def main():
    """Main entry point."""
    # Validate arguments BEFORE setting up logger to avoid polluting log files
    if len(sys.argv) < 3:
        print("ERROR: Usage: mux.py <video_file> <subtitle_file> [output_file]", file=sys.stderr)
        sys.exit(1)
    
    video_file = Path(sys.argv[1])
    subtitle_file = Path(sys.argv[2])
    
    if not video_file.exists():
        print(f"ERROR: Video file not found: {video_file}", file=sys.stderr)
        sys.exit(1)
    
    if not subtitle_file.exists():
        print(f"ERROR: Subtitle file not found: {subtitle_file}", file=sys.stderr)
        sys.exit(1)
    
    # Now load config and setup logger
    config = load_config()
    
    logger = setup_logger(
        "mux",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    # Determine output file
    if len(sys.argv) > 3:
        output_file = Path(sys.argv[3])
    else:
        # Use output_root directly (should be job-specific directory)
        output_root = Path(config.output_root)
        movie_dir = output_root
        container_format = config.get("mux_container_format", "mp4")
        output_file = movie_dir / f"final_output.{container_format}"
    
    # Run mux
    success = mux_subtitles(video_file, subtitle_file, output_file, config)
    
    if not success:
        logger.error("Mux failed")
        sys.exit(1)
    
    logger.info("Mux step completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
