#!/usr/bin/env python3
"""Stage 10: Mux - Embed subtitles into video"""
import sys
import json
import argparse
import os
from pathlib import Path
import time

sys.path.insert(0, 'native/utils')
from native_logger import NativePipelineLogger
from manifest import StageManifest
from ffmpeg_mux import FFmpegMuxer


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'subtitle_codec': os.getenv('MUX_SUBTITLE_CODEC', 'mov_text'),
        'subtitle_language': os.getenv('MUX_SUBTITLE_LANGUAGE', 'eng'),
        'subtitle_title': os.getenv('MUX_SUBTITLE_TITLE', 'English'),
        'copy_video': os.getenv('MUX_COPY_VIDEO', 'true').lower() == 'true',
        'copy_audio': os.getenv('MUX_COPY_AUDIO', 'true').lower() == 'true',
        'container_format': os.getenv('MUX_CONTAINER_FORMAT', 'mp4')
    }


def run_mux(
    video_file: Path,
    subtitle_file: Path,
    output_file: Path,
    logger,
    config: dict,
    metadata: dict = None
):
    """
    Mux subtitles into video file using FFmpeg.
    
    Args:
        video_file: Input video file
        subtitle_file: SRT subtitle file
        output_file: Output video file with embedded subtitles
        logger: Logger instance
        config: Configuration dict
        metadata: Optional metadata dict
        
    Returns:
        Dictionary with mux statistics
    """
    logger.info("Starting FFmpeg muxing process")
    logger.debug(f"Video: {video_file}")
    logger.debug(f"Subtitles: {subtitle_file}")
    logger.debug(f"Output: {output_file}")
    
    logger.info(f"Configuration:")
    logger.info(f"  Container format: {config['container_format']}")
    logger.info(f"  Subtitle codec: {config['subtitle_codec']}")
    logger.info(f"  Subtitle language: {config['subtitle_language']}")
    logger.info(f"  Subtitle title: {config['subtitle_title']}")
    logger.info(f"  Copy video: {config['copy_video']}")
    logger.info(f"  Copy audio: {config['copy_audio']}")
    
    start = time.time()
    
    try:
        # Initialize muxer
        muxer = FFmpegMuxer(logger=logger)
        
        # Get input file info
        logger.info("Analyzing input video...")
        stream_info = muxer.get_stream_info(video_file)
        
        input_size = muxer.get_file_size(video_file)
        subtitle_size = muxer.get_file_size(subtitle_file)
        
        logger.info(f"Input video size: {muxer.format_size(input_size)}")
        logger.info(f"Subtitle file size: {muxer.format_size(subtitle_size)}")
        
        # Mux subtitles
        logger.info("Muxing subtitles into video...")
        success, message = muxer.mux_subtitles(
            video_file=video_file,
            subtitle_file=subtitle_file,
            output_file=output_file,
            subtitle_language=config['subtitle_language'],
            subtitle_title=config['subtitle_title'],
            subtitle_codec=config['subtitle_codec'],
            container_format=config['container_format'],
            copy_video=config['copy_video'],
            copy_audio=config['copy_audio'],
            overwrite=True
        )
        
        if not success:
            raise RuntimeError(f"Muxing failed: {message}")
        
        duration = time.time() - start
        
        # Get output file size
        output_size = muxer.get_file_size(output_file)
        size_diff = output_size - input_size
        
        logger.log_processing("Muxing completed", duration)
        logger.info(f"Output video size: {muxer.format_size(output_size)}")
        logger.info(f"Size increase: {muxer.format_size(size_diff)} "
                   f"({(size_diff/input_size)*100:.2f}%)")
        
        # Build statistics
        stats = {
            'input_size': input_size,
            'subtitle_size': subtitle_size,
            'output_size': output_size,
            'size_increase': size_diff,
            'size_increase_percent': round((size_diff/input_size)*100, 2),
            'duration': round(duration, 2),
            'container_format': config['container_format'],
            'subtitle_codec': config['subtitle_codec'],
            'subtitle_language': config['subtitle_language'],
            'subtitle_title': config['subtitle_title'],
            'copy_video': config['copy_video'],
            'copy_audio': config['copy_audio'],
            'streams': len(stream_info.get('streams', []))
        }
        
        logger.log_metric("Processing time", f"{duration:.2f}s")
        logger.log_metric("Output size", muxer.format_size(output_size))
        logger.log_metric("Size increase", f"{stats['size_increase_percent']:.2f}%")
        
        return stats
        
    except Exception as e:
        logger.error(f"Muxing failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Stage 10: Mux subtitles into video file'
    )
    parser.add_argument('--input', required=True, 
                       help='Input video file')
    parser.add_argument('--movie-dir', required=True,
                       help='Movie output directory')
    parser.add_argument('--output-name',
                       help='Custom output filename (default: final_output.{format})')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('mux', movie_name)
    
    try:
        logger.log_stage_start("FFmpeg Muxing - Embed Subtitles")
        
        # Load configuration from environment
        env_config = load_env_config()
        
        logger.info(f"Configuration loaded from environment")
        
        with StageManifest('mux', movie_dir, logger.logger) as manifest:
            # Locate required files
            video_file = Path(args.input)
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_file}")
            
            # Find subtitle file
            subtitle_files = list(movie_dir.glob('en_merged/*.srt'))
            if not subtitle_files:
                subtitle_files = list(movie_dir.glob('en_merged/*.merged.srt'))
            
            if not subtitle_files:
                raise FileNotFoundError(f"No subtitle files found in en_merged/")
            
            subtitle_file = subtitle_files[0]
            
            logger.info(f"Input video: {video_file}")
            logger.info(f"Subtitle file: {subtitle_file}")
            
            # Determine output filename
            if args.output_name:
                output_filename = args.output_name
            else:
                container_format = env_config['container_format']
                output_filename = f'final_output.{container_format}'
            
            output_file = movie_dir / output_filename
            logger.info(f"Output file: {output_file}")
            
            # Load metadata if available
            metadata = {}
            metadata_file = movie_dir / 'metadata' / 'tmdb_metadata.json'
            if metadata_file.exists():
                logger.debug("Loading TMDB metadata...")
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    tmdb_data = json.load(f)
                    metadata = {
                        'title': tmdb_data.get('title', movie_name),
                        'year': str(tmdb_data.get('release_date', '')[:4]),
                        'genre': ', '.join(g['name'] for g in tmdb_data.get('genres', [])),
                        'comment': 'Processed with WhisperX Native Pipeline'
                    }
                    logger.debug(f"Metadata: {metadata}")
            
            # Run muxing with configuration
            stats = run_mux(
                video_file=video_file,
                subtitle_file=subtitle_file,
                output_file=output_file,
                logger=logger,
                config=env_config,
                metadata=metadata
            )
            
            # Save statistics
            stats_file = movie_dir / 'mux_stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            logger.log_file_operation("Saved mux statistics", stats_file, success=True)
            
            # Add to manifest
            manifest.add_output('final_video', output_file, 'Final video with subtitles')
            manifest.add_output('statistics', stats_file, 'Muxing statistics')
            
            manifest.add_metadata('output_size', stats['output_size'])
            manifest.add_metadata('size_increase_mb', round(stats['size_increase'] / 1024 / 1024, 2))
            manifest.add_metadata('container_format', stats['container_format'])
            manifest.add_metadata('subtitle_codec', stats['subtitle_codec'])
            manifest.add_metadata('copy_video', stats['copy_video'])
            manifest.add_metadata('copy_audio', stats['copy_audio'])
            manifest.add_metadata('subtitle_language', stats['subtitle_language'])
            manifest.add_metadata('processing_time', stats['duration'])
            
            logger.info("=" * 60)
            logger.info("✅ MUXING COMPLETE")
            logger.info(f"Final output: {output_file}")
            logger.info(f"File size: {stats['output_size'] / 1024 / 1024:.2f} MB")
            logger.info(f"Processing time: {stats['duration']:.2f}s")
            logger.info("=" * 60)
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
