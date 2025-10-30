#!/usr/bin/env python3
"""Stage 8: Post-ASR NER - Entity Correction & Enrichment"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, 'native/utils')
from native_logger import NativePipelineLogger
from manifest import StageManifest
from post_ner_wrapper import PostNER, load_secrets


def run_post_ner(
    transcript_file: Path,
    pre_ner_file: Path,
    logger,
    config: dict = None
):
    """
    Run Post-ASR NER for entity correction.
    
    Args:
        transcript_file: Path to transcript JSON from ASR
        pre_ner_file: Path to pre-NER entities JSON
        logger: Logger instance
        config: Optional config dict
        
    Returns:
        Tuple of (corrected_result, statistics)
    """
    # Default configuration
    default_config = {
        'similarity_threshold': 0.70,
        'enable_fuzzy_matching': True
    }
    
    if config:
        default_config.update(config)
    
    logger.info("Running Post-ASR NER entity correction")
    logger.debug(f"Configuration: {default_config}")
    
    # Load transcript
    if not transcript_file.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    logger.info(f"Loaded transcript with {len(transcript_data.get('segments', []))} segments")
    
    # Load pre-NER entities
    if not pre_ner_file.exists():
        logger.warning(f"Pre-NER file not found: {pre_ner_file}")
        logger.warning("Proceeding without entity corrections")
        return {
            'transcript': transcript_data,
            'corrections': [],
            'statistics': {
                'segments_processed': len(transcript_data.get('segments', [])),
                'total_corrections': 0,
                'unique_corrections': 0
            }
        }, {}
    
    import time
    start = time.time()
    
    try:
        # Initialize Post-NER
        post_ner = PostNER(logger=logger)
        
        # Load known entities
        post_ner.load_pre_ner_entities(pre_ner_file)
        
        # Process transcript
        result, stats = post_ner.process_transcript(
            transcript_data,
            min_threshold=default_config['similarity_threshold']
        )
        
        duration = time.time() - start
        
        # Log results
        logger.log_processing("Entity correction complete", duration)
        logger.log_metric("Segments processed", stats['segments_processed'])
        logger.log_metric("Total corrections", stats['total_corrections'])
        logger.log_metric("Unique corrections", stats['unique_corrections'])
        
        # Generate report
        if result['corrections']:
            report = post_ner.generate_entity_report(result['corrections'])
            logger.debug("\n" + report)
        
        return result, stats
        
    except Exception as e:
        logger.error(f"Post-NER processing failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    parser.add_argument('--threshold', type=float, default=0.70,
                       help='Similarity threshold for entity matching (0.0-1.0)')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('post-ner', movie_name)
    
    try:
        logger.log_stage_start("Post-ASR NER - Entity correction & enrichment")
        
        # Prepare config
        config = {
            'similarity_threshold': args.threshold,
            'enable_fuzzy_matching': True
        }
        
        with StageManifest('post-ner', movie_dir, logger.logger) as manifest:
            transcript_file = movie_dir / 'transcription' / 'transcript.json'
            pre_ner_file = movie_dir / 'entities' / 'pre_ner.json'
            
            if not transcript_file.exists():
                raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
            
            logger.debug(f"Transcript file: {transcript_file}")
            logger.debug(f"Pre-NER file: {pre_ner_file}")
            
            # Run Post-NER
            result, stats = run_post_ner(
                transcript_file=transcript_file,
                pre_ner_file=pre_ner_file,
                logger=logger,
                config=config
            )
            
            # Create output directory
            entities_dir = movie_dir / 'entities'
            entities_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Entities directory: {entities_dir}")
            
            # Save corrected transcript
            corrected_transcript_file = movie_dir / 'transcription' / 'transcript_corrected.json'
            with open(corrected_transcript_file, 'w', encoding='utf-8') as f:
                json.dump(result['transcript'], f, indent=2, ensure_ascii=False)
            
            logger.log_file_operation("Saved corrected transcript", 
                                     corrected_transcript_file, success=True)
            
            # Save corrections report
            corrections_file = entities_dir / 'post_ner_corrections.json'
            corrections_data = {
                'corrections': result['corrections'],
                'statistics': result['statistics'],
                'config': config
            }
            
            with open(corrections_file, 'w', encoding='utf-8') as f:
                json.dump(corrections_data, f, indent=2, ensure_ascii=False)
            
            logger.log_file_operation("Saved corrections report", 
                                     corrections_file, success=True)
            
            # Save human-readable report
            report_file = entities_dir / 'post_ner_report.txt'
            if result['corrections']:
                from post_ner_wrapper import PostNER
                post_ner = PostNER()
                report = post_ner.generate_entity_report(result['corrections'])
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.log_file_operation("Saved text report", report_file, success=True)
            
            # Add to manifest
            manifest.add_output('corrected_transcript', corrected_transcript_file,
                              'Transcript with corrected entities')
            manifest.add_output('corrections', corrections_file,
                              'Entity corrections report')
            if result['corrections']:
                manifest.add_output('report', report_file,
                                  'Human-readable corrections report')
            
            manifest.add_metadata('segments_processed', stats['segments_processed'])
            manifest.add_metadata('total_corrections', stats['total_corrections'])
            manifest.add_metadata('unique_corrections', stats['unique_corrections'])
            manifest.add_metadata('threshold', config['similarity_threshold'])
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
