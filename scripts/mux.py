#!/usr/bin/env python3
"""
Mux stage: Combine video with subtitles
"""
import sys
import os
import subprocess
from pathlib import Path
import json

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO
from shared.logger import PipelineLogger

def main():
    # Load configuration from environment or command-line arguments
    config_path = os.environ.get('CONFIG_PATH')
    if config_path:
        config_path = Path(config_path)
    elif len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    else:
        config_path = Path("config/.env.pipeline")
    
    output_dir_env = os.environ.get('OUTPUT_DIR')
    if output_dir_env:
        output_dir = Path(output_dir_env)
    elif len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path("out")
    
    # Initialize StageIO
    stage_io = StageIO("mux", output_base=output_dir)
    
    # Setup logger
    log_file = stage_io.get_log_path()
    logger = PipelineLogger("mux", log_file)
    
    logger.info("Running mux stage")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Read config
    logger.info(f"Reading config from: {config_path}")
    with open(config_path, 'r', encoding='utf-8', errors='replace') as f:
        config = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"')
    
    input_file = config.get('IN_ROOT', config.get('INPUT_MEDIA', ''))
    if not input_file or not Path(input_file).exists():
        logger.error(f"Input media not found: {input_file}")
        return 1
    
    logger.info(f"Input media: {input_file}")
    
    # Check for subtitle file - try multiple locations
    # After refactor: subtitle_gen is now stage 14
    subtitle_file = output_dir / "14_subtitle_gen" / "subtitles.srt"
    if not subtitle_file.exists():
        subtitle_file = output_dir / "subtitles" / "subtitles.srt"
    if not subtitle_file.exists():
        subtitle_file = output_dir / "subtitles.srt"
    
    if not subtitle_file.exists():
        logger.error(f"Subtitle file not found in expected locations")
        logger.error(f"  Tried: {output_dir / '14_subtitle_gen' / 'subtitles.srt'}")
        logger.error(f"  Tried: {output_dir / 'subtitles' / 'subtitles.srt'}")
        logger.error(f"  Tried: {output_dir / 'subtitles.srt'}")
        return 1
    
    logger.info(f"Subtitle file: {subtitle_file}")
    
    # Output video file - preserve original filename and format
    # Extract original filename and extension
    input_path = Path(input_file)
    original_name = input_path.stem  # Filename without extension
    original_ext = input_path.suffix  # Extension including dot (e.g., '.mp4')
    
    # Create movie-specific subdirectory within mux stage
    movie_dir = stage_io.stage_dir / original_name
    movie_dir.mkdir(parents=True, exist_ok=True)
    
    # Use original filename with subtitle suffix, preserve format
    output_filename = f"{original_name}_subtitled{original_ext}"
    output_file = movie_dir / output_filename
    
    logger.info(f"Original file: {input_path.name}")
    logger.info(f"Output format: {original_ext} (preserved from original)")
    logger.info(f"Movie directory: {movie_dir}")
    
    # Mux video with subtitles using ffmpeg
    # For MP4: use mov_text codec, for MKV/WebM: use srt codec, for other: try both
    if original_ext.lower() in ['.mp4', '.m4v']:
        subtitle_codec = "mov_text"
        logger.info(f"Using mov_text codec for MP4 container")
    elif original_ext.lower() in ['.mkv', '.webm']:
        subtitle_codec = "srt"
        logger.info(f"Using srt codec for {original_ext} container")
    else:
        # Default to srt for unknown formats
        subtitle_codec = "srt"
        logger.info(f"Using srt codec (default) for {original_ext} container")
    
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-i", str(subtitle_file),
        "-c:v", "copy",  # Copy video stream
        "-c:a", "copy",  # Copy audio stream
        "-c:s", subtitle_codec,  # Subtitle codec based on container
        "-metadata:s:s:0", "language=eng",
        "-disposition:s:0", "default",  # Mark subtitle stream as default
        "-y",  # Overwrite
        str(output_file)
    ]
    
    logger.info(f"Muxing video with subtitles")
    logger.info(f"  Output: {output_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"ffmpeg failed with code {result.returncode}")
        logger.error(f"stderr: {result.stderr}")
        return 1
    
    logger.info(f"✓ Video muxed successfully")
    
    # Create final_output.mp4 symlink at job directory root
    final_output_link = output_dir / "final_output.mp4"
    try:
        # Remove existing symlink/file if present
        if final_output_link.exists() or final_output_link.is_symlink():
            final_output_link.unlink()
        
        # Create symlink to muxed file
        final_output_link.symlink_to(output_file.relative_to(output_dir))
        logger.info(f"✓ Created final_output.mp4 link")
    except Exception as e:
        logger.warning(f"Could not create final_output link: {e}")
    
    # Save metadata
    metadata = {
        "status": "completed",
        "input_file": str(input_file),
        "subtitle_file": str(subtitle_file),
        "output_file": str(output_file)
    }
    stage_io.save_metadata(metadata)
    
    # Update manifest
    manifest_file = output_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8', errors='replace') as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    manifest.setdefault('stages', {})['mux'] = {
        'status': 'completed',
        'output_file': str(output_file)
    }
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
