#!/usr/bin/env python3
"""Stage 1: Demux - Extract audio from video using FFmpeg"""
import sys
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, 'native/utils')
sys.path.insert(0, 'shared')

from native_logger import NativePipelineLogger
from manifest import StageManifest

def get_movie_dir(input_file, output_root):
    """Get movie-specific output directory"""
    name = Path(input_file).stem.replace(' ', '_')
    return Path(output_root) / name

def demux_audio(input_file, output_file, logger):
    """Extract 16kHz mono audio using FFmpeg"""
    logger.info(f"Extracting audio to: {output_file}")
    logger.debug(f"Input file: {input_file}")
    
    cmd = [
        'ffmpeg', '-i', str(input_file),
        '-vn',  # No video
        '-acodec', 'pcm_s16le',
        '-ar', '16000',  # 16kHz
        '-ac', '1',  # Mono
        '-y',  # Overwrite
        str(output_file)
    ]
    
    logger.debug(f"FFmpeg command: {' '.join(cmd)}")
    
    import time
    start = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = time.time() - start
        logger.log_processing("Audio extraction complete", duration)
        logger.log_file_operation("Created audio file", output_file, success=True)
        
        # Log output file details
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.log_metric("Audio file size", f"{file_size_mb:.2f}", "MB")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr}")
        logger.error(f"Return code: {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('demux', movie_name)
    
    try:
        logger.log_stage_start("FFmpeg audio extraction (16kHz mono)")
        
        with StageManifest('demux', movie_dir, logger.logger) as manifest:
            audio_dir = movie_dir / 'audio'
            audio_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created audio directory: {audio_dir}")
            
            output_file = audio_dir / 'audio.wav'
            
            if not demux_audio(args.input, output_file, logger):
                logger.log_stage_end(success=False)
                raise Exception("Audio extraction failed")
            
            manifest.add_output('audio', output_file, '16kHz mono audio')
            manifest.add_metadata('sample_rate', 16000)
            manifest.add_metadata('channels', 1)
            manifest.add_metadata('format', 'wav')
            manifest.add_metadata('file_size_mb', output_file.stat().st_size / (1024*1024))
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise

if __name__ == '__main__':
    main()
