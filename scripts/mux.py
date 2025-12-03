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

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

def main():
    stage_io = None
    logger = None
    
    try:
        # Initialize StageIO with manifest tracking
        stage_io = StageIO("mux", enable_manifest=True)
        logger = stage_io.get_stage_logger("INFO")
    
    logger.info("=" * 60)
    logger.info("MUX STAGE: Combine Video with Subtitles")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        stage_io.add_error(f"Config load failed: {e}", e)
        stage_io.finalize(status="failed", error=str(e))
        return 1
    
    logger.info(f"Output directory: {stage_io.output_base}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Get input file from config
    input_file = getattr(config, 'in_root', getattr(config, 'input_media', ''))
    if not input_file or not Path(input_file).exists():
        logger.error(f"Input media not found: {input_file}")
        stage_io.add_error(f"Input media not found: {input_file}")
        stage_io.finalize(status="failed", error="Input file missing")
        return 1
    
    # Track input video
    input_path = Path(input_file)
    stage_io.track_input(input_path, "video", format=input_path.suffix[1:])
    
    logger.info(f"Input media: {input_file}")
    
    # Find all subtitle files - check multiple locations
    output_base = stage_io.output_base
    subtitle_locations = [
        output_base / "subtitles",
        output_base / "11_subtitle_generation",
        output_base
    ]
    
    subtitle_files = []
    for location in subtitle_locations:
        if location.exists():
            # Find all .srt files in this location
            srt_files = list(location.glob("*.srt"))
            if srt_files:
                subtitle_files.extend(srt_files)
                break  # Use first location that has .srt files
    
    if not subtitle_files:
        logger.error(f"No subtitle files found")
        logger.error(f"  Searched: {', '.join(str(loc) for loc in subtitle_locations)}")
        stage_io.add_error("No subtitle files found")
        stage_io.finalize(status="failed", error="No subtitles")
        return 1
    
    # Track subtitle inputs
    for sub_file in subtitle_files:
        stage_io.track_input(sub_file, "subtitle", format="srt")
    
    # Sort subtitle files by language (prioritize: hi, en, then others)
    def sort_key(path):
        name = path.stem.lower()
        if '.hi.' in name or name.endswith('.hi'):
            return (0, path.stem)  # Hindi first
        elif '.en.' in name or name.endswith('.en'):
            return (1, path.stem)  # English second
        else:
            return (2, path.stem)  # Others last
    
    subtitle_files = sorted(subtitle_files, key=sort_key)
    
    logger.info(f"Found {len(subtitle_files)} subtitle file(s):")
    for sub_file in subtitle_files:
        logger.info(f"  - {sub_file.name}")
    
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
    
    # Track configuration
    stage_io.set_config({
        "subtitle_codec": "auto",  # Will be set below
        "subtitle_count": len(subtitle_files),
        "container_format": original_ext
    })
    
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
    
    # Update config with actual codec
    stage_io.set_config({"subtitle_codec": subtitle_codec})
    
    # Build ffmpeg command with multiple subtitle inputs
    cmd = ["ffmpeg", "-i", str(input_file)]
    
    # Add each subtitle file as an input
    for sub_file in subtitle_files:
        cmd.extend(["-i", str(sub_file)])
    
    # Copy video and audio streams
    cmd.extend(["-c:v", "copy", "-c:a", "copy"])
    
    # Set subtitle codec for all subtitle streams
    cmd.extend(["-c:s", subtitle_codec])
    
    # Add metadata for each subtitle stream
    # Extract language code from filename (e.g., "movie.hi.srt" -> "hi")
    for idx, sub_file in enumerate(subtitle_files):
        stem = sub_file.stem  # e.g., "Jaane Tu Ya Jaane Na.hi"
        parts = stem.split('.')
        
        # Try to extract language code (last part before extension)
        if len(parts) >= 2:
            lang_code = parts[-1].lower()  # e.g., "hi", "en", "gu"
        else:
            lang_code = "und"  # undefined
        
        # Map 2-letter codes to 3-letter ISO 639-2 codes for better compatibility
        lang_map = {
            "hi": "hin",  # Hindi
            "en": "eng",  # English
            "gu": "guj",  # Gujarati
            "ta": "tam",  # Tamil
            "te": "tel",  # Telugu
            "bn": "ben",  # Bengali
            "mr": "mar",  # Marathi
            "kn": "kan",  # Kannada
            "ml": "mal",  # Malayalam
            "pa": "pan",  # Punjabi
            "ur": "urd",  # Urdu
        }
        
        lang_code_3 = lang_map.get(lang_code, lang_code)
        
        # Set language metadata
        cmd.extend([f"-metadata:s:s:{idx}", f"language={lang_code_3}"])
        
        # Set title metadata (for display in players)
        lang_names = {
            "hin": "Hindi",
            "eng": "English",
            "guj": "Gujarati",
            "tam": "Tamil",
            "tel": "Telugu",
            "ben": "Bengali",
            "mar": "Marathi",
            "kan": "Kannada",
            "mal": "Malayalam",
            "pan": "Punjabi",
            "urd": "Urdu",
        }
        lang_title = lang_names.get(lang_code_3, lang_code_3.upper())
        cmd.extend([f"-metadata:s:s:{idx}", f"title={lang_title}"])
        
        logger.info(f"  Subtitle track {idx}: {lang_title} ({lang_code_3})")
    
    # Mark first subtitle as default (usually Hindi or source language)
    cmd.extend(["-disposition:s:0", "default"])
    
    # Map all streams
    cmd.extend(["-map", "0:v", "-map", "0:a"])
    for idx in range(len(subtitle_files)):
        cmd.extend(["-map", f"{idx+1}:s"])
    
    cmd.extend(["-y", str(output_file)])
    
    logger.info(f"Muxing video with subtitles")
    logger.info(f"  Output: {output_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"ffmpeg failed with code {result.returncode}")
        logger.error(f"stderr: {result.stderr}")
        stage_io.add_error(f"ffmpeg failed: {result.stderr[:200]}")
        stage_io.finalize(status="failed", error="Muxing failed")
        return 1
    
    logger.info(f"✓ Video muxed successfully")
    
    # Track output
    output_size_mb = output_file.stat().st_size / (1024*1024) if output_file.exists() else 0
    stage_io.track_output(output_file, "video",
                         format=original_ext[1:],
                         subtitle_tracks=len(subtitle_files),
                         size_mb=round(output_size_mb, 2))
    
    # Create final_output.mp4 symlink at job directory root
    output_dir = stage_io.output_base
    final_output_link = output_dir / "final_output.mp4"
    try:
        # Remove existing symlink/file if present
        if final_output_link.exists() or final_output_link.is_symlink():
            final_output_link.unlink()
        
        # Create symlink to muxed file
        final_output_link.symlink_to(output_file.relative_to(output_dir))
        logger.info(f"✓ Created final_output.mp4 link")
        
        # Track symlink as intermediate
        stage_io.track_intermediate(final_output_link, retained=True,
                                   reason="Convenience symlink to final output")
    except Exception as e:
        logger.warning(f"Could not create final_output link: {e}")
        stage_io.add_warning(f"Symlink creation failed: {e}")
    
    # Save metadata
    metadata = {
        "status": "completed",
        "input_file": str(input_file),
        "subtitle_files": [str(f) for f in subtitle_files],
        "subtitle_count": len(subtitle_files),
        "output_file": str(output_file)
    }
    metadata_file = stage_io.save_metadata(metadata)
    stage_io.track_intermediate(metadata_file, retained=True,
                               reason="Stage metadata")
    
    # Finalize with success
    stage_io.finalize(status="success",
                     subtitle_tracks=len(subtitle_files),
                     output_size_mb=round(output_size_mb, 2),
                     codec=subtitle_codec)
    
    logger.info("=" * 60)
    logger.info("MUX STAGE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Final video: {output_file}")
    logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
    logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
    
        return 0
    
    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"File not found: {e}")
            stage_io.finalize(status="failed", error=f"Missing file: {e}")
        return 1
    
    except IOError as e:
        if logger:
            logger.error(f"I/O error: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"I/O error: {e}")
            stage_io.finalize(status="failed", error=f"IO error: {e}")
        return 1
    
    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(f"ffmpeg command failed: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"ffmpeg error: {e}")
            stage_io.finalize(status="failed", error="Muxing process failed")
        return 1
    
    except ValueError as e:
        if logger:
            logger.error(f"Invalid value: {e}", exc_info=True, exc_info=True)
        if stage_io:
            stage_io.add_error(f"Validation error: {e}")
            stage_io.finalize(status="failed", error=f"Invalid input: {e}")
        return 1
    
    except KeyboardInterrupt:
        if logger:
            logger.warning("Interrupted by user")
        if stage_io:
            stage_io.add_error("User interrupted")
            stage_io.finalize(status="failed", error="User interrupted")
        return 130
    
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}", exc_info=True, exc_info=True)
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        if stage_io:
            stage_io.add_error(f"Unexpected error: {e}")
            stage_io.finalize(status="failed", error=f"Unexpected: {type(e).__name__}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
