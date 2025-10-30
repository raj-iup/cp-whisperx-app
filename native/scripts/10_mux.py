#!/usr/bin/env python3
"""Stage 10: Mux - Embed subtitles into video"""
import sys
import json
import argparse
from pathlib import Path
import time

sys.path.insert(0, 'native/utils')
from native_logger import NativePipelineLogger
from manifest import StageManifest
from ffmpeg_mux import FFmpegMuxer


def run_mux(
    video_file: Path,
    subtitle_file: Path,
    output_file: Path,
    logger,
    metadata: dict = None,
    container_format: str = 'mp4',
    subtitle_language: str = 'eng',
    subtitle_title: str = 'English'
):
    """
    Mux subtitles into video file using FFmpeg.
    
    Args:
        video_file: Input video file
        subtitle_file: SRT subtitle file
        output_file: Output video file with embedded subtitles
        logger: Logger instance
        metadata: Optional metadata dict
        container_format: Output container format (mp4 or mkv)
        subtitle_language: ISO 639-2 language code
        subtitle_title: Subtitle track title
        
    Returns:
        Dictionary with mux statistics
    """
    logger.info("Starting FFmpeg muxing process")
    logger.debug(f"Video: {video_file}")
    logger.debug(f"Subtitles: {subtitle_file}")
    logger.debug(f"Output: {output_file}")
    logger.debug(f"Format: {container_format}")
    
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
            subtitle_language=subtitle_language,
            subtitle_title=subtitle_title,
            container_format=container_format,
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
            'container_format': container_format,
            'subtitle_language': subtitle_language,
            'subtitle_title': subtitle_title,
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
    parser.add_argument('--format', default='mp4', choices=['mp4', 'mkv'],
                       help='Output container format (default: mp4)')
    parser.add_argument('--subtitle-lang', default='eng',
                       help='Subtitle language code (default: eng)')
    parser.add_argument('--subtitle-title', default='English',
                       help='Subtitle track title (default: English)')
    parser.add_argument('--output-name',
                       help='Custom output filename (default: {movie_name}_subtitled.{format})')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('mux', movie_name)
    
    try:
        logger.log_stage_start("FFmpeg Muxing - Embed Subtitles")
        
        with StageManifest('mux', movie_dir, logger.logger) as manifest:
            # Locate required files
            video_file = Path(args.input)
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_file}")
            
            # Find subtitle file
            subtitles_dir = movie_dir / 'subtitles'
            subtitle_file = subtitles_dir / f'{movie_name}.srt'
            
            if not subtitle_file.exists():
                raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")
            
            logger.info(f"Input video: {video_file}")
            logger.info(f"Subtitle file: {subtitle_file}")
            
            # Determine output filename
            if args.output_name:
                output_filename = args.output_name
            else:
                output_filename = f'{movie_name}_subtitled.{args.format}'
            
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
                        'comment': 'Processed with WhisperX Native MPS Pipeline'
                    }
                    logger.debug(f"Metadata: {metadata}")
            
            # Run muxing
            stats = run_mux(
                video_file=video_file,
                subtitle_file=subtitle_file,
                output_file=output_file,
                logger=logger,
                metadata=metadata,
                container_format=args.format,
                subtitle_language=args.subtitle_lang,
                subtitle_title=args.subtitle_title
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
