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
    
    logger.info(f"Starting mux")
    logger.info(f"Video: {video_file.name}")
    logger.info(f"Subtitles: {subtitle_file.name}")
    logger.info(f"Output: {output_file}")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-i", str(subtitle_file),
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", config.get("mux_subtitle_codec", "mov_text"),
            "-metadata:s:s:0", f"language={config.get('mux_subtitle_language', 'eng')}",
            "-metadata:s:s:0", f"title={config.get('mux_subtitle_title', 'English')}",
            str(output_file)
        ]
        
        logger.debug(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Mux completed successfully")
        logger.info(f"Output size: {output_file.stat().st_size / (1024*1024):.2f} MB")
        
        # Save metadata
        metadata = {
            "video_file": str(video_file),
            "subtitle_file": str(subtitle_file),
            "output_file": str(output_file),
            "subtitle_codec": config.get("mux_subtitle_codec", "mov_text"),
            "subtitle_language": config.get("mux_subtitle_language", "eng"),
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
    config = load_config()
    
    logger = setup_logger(
        "mux",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    # Get paths from command line
    if len(sys.argv) < 3:
        logger.error("Usage: mux.py <video_file> <subtitle_file> [output_file]")
        sys.exit(1)
    
    video_file = Path(sys.argv[1])
    subtitle_file = Path(sys.argv[2])
    
    if len(sys.argv) > 3:
        output_file = Path(sys.argv[3])
    else:
        # Use movie directory structure
        movie_dir = get_movie_dir(video_file, Path(config.output_root))
        output_file = movie_dir / f"{movie_dir.name}_with_subs.mp4"
    
    # Validate inputs
    if not video_file.exists():
        logger.error(f"Video file not found: {video_file}")
        sys.exit(1)
    
    if not subtitle_file.exists():
        logger.error(f"Subtitle file not found: {subtitle_file}")
        sys.exit(1)
    
    # Run mux
    success = mux_subtitles(video_file, subtitle_file, output_file, config)
    
    if not success:
        logger.error("Mux failed")
        sys.exit(1)
    
    logger.info("Mux step completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
