#!/usr/bin/env python3
"""Stage 9: Subtitle Generation (.srt format)"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, 'native/utils')
from native_logger import NativePipelineLogger
from manifest import StageManifest
from subtitle_generator import SubtitleGenerator


def run_subtitle_generation(
    transcript_file: Path,
    logger,
    config: dict = None
):
    """
    Generate SRT subtitles from transcript.
    
    Args:
        transcript_file: Path to transcript JSON (corrected or original)
        logger: Logger instance
        config: Optional config dict
        
    Returns:
        Tuple of (srt_content, statistics)
    """
    # Default configuration
    default_config = {
        'include_speaker': True,
        'merge_short': True,
        'split_long': True,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'max_chars': 84,
        'max_chars_per_line': 42,
        'max_lines': 2
    }
    
    if config:
        default_config.update(config)
    
    logger.info("Generating SRT subtitles")
    logger.debug(f"Configuration: {default_config}")
    
    # Load transcript
    if not transcript_file.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    logger.info(f"Loaded transcript with {len(transcript_data.get('segments', []))} segments")
    
    import time
    start = time.time()
    
    try:
        # Initialize subtitle generator
        generator = SubtitleGenerator(logger=logger)
        
        # Process transcript and generate SRT
        srt_content, stats = generator.process_transcript(
            transcript_data,
            config=default_config
        )
        
        duration = time.time() - start
        
        # Log results
        logger.log_processing("Subtitle generation complete", duration)
        logger.log_metric("Original segments", stats['original_segments'])
        logger.log_metric("Processed segments", stats['processed_segments'])
        logger.log_metric("Total subtitles", stats['total_subtitles'])
        logger.log_metric("Total duration", f"{stats['total_duration']:.2f}s")
        logger.log_metric("Avg subtitle duration", f"{stats['avg_subtitle_duration']:.2f}s")
        logger.log_metric("Unique speakers", stats['speakers'])
        
        return srt_content, stats
        
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    parser.add_argument('--use-corrected', action='store_true',
                       help='Use entity-corrected transcript (default: True)')
    parser.add_argument('--no-speaker', action='store_true',
                       help='Exclude speaker labels from subtitles')
    parser.add_argument('--no-merge', action='store_true',
                       help='Disable merging of short segments')
    parser.add_argument('--no-split', action='store_true',
                       help='Disable splitting of long segments')
    parser.add_argument('--max-duration', type=float, default=7.0,
                       help='Maximum subtitle duration in seconds (default: 7.0)')
    parser.add_argument('--max-chars', type=int, default=84,
                       help='Maximum characters per subtitle (default: 84)')
    parser.add_argument('--max-chars-per-line', type=int, default=42,
                       help='Maximum characters per line (default: 42)')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('subtitle-gen', movie_name)
    
    try:
        logger.log_stage_start("SRT Subtitle Generation")
        
        # Prepare config
        config = {
            'include_speaker': not args.no_speaker,
            'merge_short': not args.no_merge,
            'split_long': not args.no_split,
            'min_duration': 1.0,
            'max_duration': args.max_duration,
            'max_chars': args.max_chars,
            'max_chars_per_line': args.max_chars_per_line,
            'max_lines': 2
        }
        
        with StageManifest('subtitle-gen', movie_dir, logger.logger) as manifest:
            # Determine which transcript to use
            corrected_transcript = movie_dir / 'transcription' / 'transcript_corrected.json'
            original_transcript = movie_dir / 'transcription' / 'transcript.json'
            
            # Prefer corrected if it exists and not explicitly disabled
            if args.use_corrected and corrected_transcript.exists():
                transcript_file = corrected_transcript
                logger.info("Using entity-corrected transcript")
            elif original_transcript.exists():
                transcript_file = original_transcript
                logger.info("Using original transcript")
            else:
                raise FileNotFoundError("No transcript file found")
            
            logger.debug(f"Transcript file: {transcript_file}")
            
            # Run subtitle generation
            srt_content, stats = run_subtitle_generation(
                transcript_file=transcript_file,
                logger=logger,
                config=config
            )
            
            # Create output directory
            subtitles_dir = movie_dir / 'subtitles'
            subtitles_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Subtitles directory: {subtitles_dir}")
            
            # Save SRT file
            srt_file = subtitles_dir / f'{movie_name}.srt'
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.log_file_operation("Saved SRT subtitles", srt_file, success=True)
            
            # Save statistics
            stats_file = subtitles_dir / 'subtitle_stats.json'
            stats_data = {
                'statistics': stats,
                'config': config,
                'source_transcript': str(transcript_file.relative_to(movie_dir))
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2)
            
            logger.log_file_operation("Saved statistics", stats_file, success=True)
            
            # Add to manifest
            manifest.add_output('subtitles', srt_file, 'SRT subtitle file')
            manifest.add_output('statistics', stats_file, 'Subtitle generation statistics')
            
            manifest.add_metadata('total_subtitles', stats['total_subtitles'])
            manifest.add_metadata('total_duration', stats['total_duration'])
            manifest.add_metadata('include_speaker', config['include_speaker'])
            manifest.add_metadata('source_transcript', 
                                'corrected' if 'corrected' in transcript_file.name else 'original')
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
