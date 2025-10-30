#!/usr/bin/env python3
"""
FFmpeg Demux Step
Extracts 16kHz mono audio from input video file.
Outputs to: out/{movie}/audio/
"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, '/app/shared')
from config import load_config
from logger import setup_logger
from utils import save_json, get_movie_dir
from manifest import StageManifest


def demux_audio(input_file: Path, output_file: Path, config) -> bool:
    """
    Extract audio from video using FFmpeg.
    
    Args:
        input_file: Path to input video
        output_file: Path to output audio file
        config: Pipeline configuration
    
    Returns:
        True if successful, False otherwise
    """
    logger = setup_logger(
        "demux",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    logger.info(f"Starting demux: {input_file.name}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Sample rate: {config.audio_sample_rate}Hz")
    logger.info(f"Channels: {config.audio_channels}")
    logger.info(f"Format: {config.audio_format}")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_file),
            "-ar", str(config.audio_sample_rate),
            "-ac", str(config.audio_channels),
            "-c:a", config.audio_codec,
            str(output_file)
        ]
        
        logger.debug(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Demux completed successfully")
        logger.info(f"Output size: {output_file.stat().st_size / (1024*1024):.2f} MB")
        
        # Save metadata
        metadata = {
            "input_file": str(input_file),
            "output_file": str(output_file),
            "sample_rate": config.audio_sample_rate,
            "channels": config.audio_channels,
            "format": config.audio_format,
            "codec": config.audio_codec,
            "file_size_mb": output_file.stat().st_size / (1024*1024)
        }
        
        metadata_file = output_file.parent / f"{output_file.stem}_demux_metadata.json"
        save_json(metadata, metadata_file)
        logger.info(f"Metadata saved: {metadata_file}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Demux failed: {e}")
        return False


def main():
    """Main entry point with manifest tracking."""
    config = load_config()
    
    logger = setup_logger(
        "demux",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    # Get input/output from environment or command line
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = Path(config.input_file)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Get movie-specific output directory
    output_root = Path(config.output_root)
    movie_dir = get_movie_dir(input_file, output_root)
    logger.info(f"Movie directory: {movie_dir}")
    
    # Create audio output directory
    audio_dir = movie_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_file = audio_dir / f"audio.{config.audio_format}"
    
    # Use manifest tracking with context manager for graceful exit
    try:
        with StageManifest("demux", movie_dir, logger) as manifest:
            logger.info(f"Starting demux: {input_file.name}")
            
            # Run demux
            success = demux_audio(input_file, output_file, config)
            
            if not success:
                raise Exception("Demux processing failed")
            
            # Record outputs in manifest
            manifest.add_output("audio", output_file, "16kHz mono audio")
            
            metadata_file = output_file.parent / f"{output_file.stem}_demux_metadata.json"
            if metadata_file.exists():
                manifest.add_output("metadata", metadata_file, "Audio metadata")
            
            # Record metadata
            manifest.add_metadata("sample_rate", config.audio_sample_rate)
            manifest.add_metadata("channels", config.audio_channels)
            manifest.add_metadata("format", config.audio_format)
            manifest.add_metadata("codec", config.audio_codec)
            manifest.add_metadata("file_size_mb", output_file.stat().st_size / (1024*1024))
            
            logger.info("✓ Demux step completed successfully")
            # Context manager will save manifest with success status
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Demux failed: {e}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
