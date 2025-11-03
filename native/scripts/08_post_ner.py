#!/usr/bin/env python3
"""Stage 8: Post-ASR NER - Entity Correction & Enrichment"""
import sys
import json
import argparse
import os
from pathlib import Path

sys.path.insert(0, 'native/utils')
from native_logger import NativePipelineLogger
from manifest import StageManifest


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'model_name': os.getenv('POST_NER_MODEL', 'en_core_web_trf'),
        'device': os.getenv('POST_NER_DEVICE', 'cpu'),
        'entity_correction': os.getenv('POST_NER_ENTITY_CORRECTION', 'true').lower() == 'true',
        'tmdb_matching': os.getenv('POST_NER_TMDB_MATCHING', 'true').lower() == 'true',
        'confidence_threshold': float(os.getenv('POST_NER_CONFIDENCE_THRESHOLD', '0.8'))
    }


def load_reference_entities(movie_dir: Path, tmdb_enabled: bool, logger) -> list:
    """Load reference entities from TMDB and Pre-NER."""
    entities = []
    
    # Load TMDB entities if enabled
    if tmdb_enabled:
        tmdb_file = movie_dir / "metadata" / "tmdb.json"
        if tmdb_file.exists():
            try:
                with open(tmdb_file, 'r') as f:
                    tmdb_data = json.load(f)
                
                # Extract cast names
                cast = tmdb_data.get("cast", [])
                entities.extend([c.get("name") for c in cast if c.get("name")])
                
                # Extract crew names
                crew = tmdb_data.get("crew", [])
                entities.extend([c.get("name") for c in crew if c.get("name")])
                
                logger.info(f"Loaded {len(entities)} entities from TMDB")
            except Exception as e:
                logger.warning(f"Failed to load TMDB entities: {e}")
        else:
            logger.warning("TMDB file not found")
    else:
        logger.info("TMDB matching disabled")
    
    # Load Pre-NER entities
    pre_ner_file = movie_dir / "pre_ner" / "entities.json"
    if pre_ner_file.exists():
        try:
            with open(pre_ner_file, 'r') as f:
                pre_ner_data = json.load(f)
            pre_ner_entities = pre_ner_data.get("entities", [])
            entities.extend(pre_ner_entities)
            logger.info(f"Loaded {len(pre_ner_entities)} entities from Pre-NER")
        except Exception as e:
            logger.warning(f"Failed to load Pre-NER entities: {e}")
    else:
        logger.warning("Pre-NER file not found")
    
    # Deduplicate
    entities = list(set(entities))
    return entities


def correct_entities_fuzzy(segments: list, reference_entities: list, threshold: float, logger) -> tuple:
    """Correct entity spellings using fuzzy matching."""
    from rapidfuzz import fuzz, process
    
    corrected_segments = []
    corrections_made = 0
    unique_corrections = set()
    
    # Convert threshold to 0-100 scale
    fuzzy_threshold = int(threshold * 100)
    
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            corrected_segments.append(segment)
            continue
        
        # Simple word-by-word fuzzy matching
        # In production, this would use NER to identify entities first
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip short words
            if len(word) < 4:
                corrected_words.append(word)
                continue
            
            # Check if word is close to any reference entity
            if reference_entities:
                result = process.extractOne(
                    word,
                    reference_entities,
                    scorer=fuzz.ratio
                )
                
                if result and result[1] >= fuzzy_threshold:
                    corrected_word = result[0]
                    if corrected_word != word:
                        logger.debug(f"Correcting '{word}' → '{corrected_word}' (score: {result[1]})")
                        corrections_made += 1
                        unique_corrections.add(f"{word}→{corrected_word}")
                        corrected_words.append(corrected_word)
                    else:
                        corrected_words.append(word)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        # Update segment with corrected text
        new_segment = segment.copy()
        new_segment["text"] = " ".join(corrected_words)
        corrected_segments.append(new_segment)
    
    stats = {
        'segments_processed': len(segments),
        'total_corrections': corrections_made,
        'unique_corrections': len(unique_corrections)
    }
    
    return corrected_segments, stats


def run_post_ner(
    transcript_file: Path,
    movie_dir: Path,
    logger,
    config: dict = None
):
    """
    Run Post-ASR NER for entity correction.
    
    Args:
        transcript_file: Path to transcript JSON from ASR
        movie_dir: Movie directory
        logger: Logger instance
        config: Configuration dict
        
    Returns:
        Tuple of (corrected_segments, statistics)
    """
    logger.info(f"Running Post-ASR NER with configuration:")
    logger.info(f"  Model: {config['model_name']}")
    logger.info(f"  Device: {config['device']}")
    logger.info(f"  Entity correction: {config['entity_correction']}")
    logger.info(f"  TMDB matching: {config['tmdb_matching']}")
    logger.info(f"  Confidence threshold: {config['confidence_threshold']}")
    
    # Load transcript
    if not transcript_file.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    # Extract segments
    if isinstance(transcript_data, dict):
        segments = transcript_data.get('segments', [])
    elif isinstance(transcript_data, list):
        segments = transcript_data
    else:
        raise ValueError("Unknown transcript format")
    
    logger.info(f"Loaded transcript with {len(segments)} segments")
    
    # Check if entity correction is enabled
    if not config['entity_correction']:
        logger.info("Entity correction disabled - returning original segments")
        return segments, {
            'segments_processed': len(segments),
            'total_corrections': 0,
            'unique_corrections': 0
        }
    
    # Load reference entities
    reference_entities = load_reference_entities(
        movie_dir,
        config['tmdb_matching'],
        logger
    )
    
    logger.info(f"Total reference entities: {len(reference_entities)}")
    
    if not reference_entities:
        logger.warning("No reference entities found - skipping corrections")
        return segments, {
            'segments_processed': len(segments),
            'total_corrections': 0,
            'unique_corrections': 0
        }
    
    import time
    start = time.time()
    
    # Perform entity correction
    corrected_segments, stats = correct_entities_fuzzy(
        segments,
        reference_entities,
        config['confidence_threshold'],
        logger
    )
    
    duration = time.time() - start
    
    # Log results
    logger.log_processing("Entity correction complete", duration)
    logger.log_metric("Segments processed", stats['segments_processed'])
    logger.log_metric("Total corrections", stats['total_corrections'])
    logger.log_metric("Unique corrections", stats['unique_corrections'])
    
    return corrected_segments, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('post_ner', movie_name)
    
    try:
        logger.log_stage_start("Post-ASR NER - Entity correction")
        
        # Load configuration from environment
        env_config = load_env_config()
        
        logger.info(f"Configuration loaded from environment")
        
        import time
        start = time.time()
        
        with StageManifest('post_ner', movie_dir, logger.logger) as manifest:
            # Get paths
            asr_files = list(movie_dir.glob('asr/*.asr.json'))
            if not asr_files:
                raise FileNotFoundError("No ASR transcript found")
            
            transcript_file = asr_files[0]
            logger.debug(f"Transcript file: {transcript_file}")
            
            # Run Post-ASR NER with configuration
            corrected_segments, stats = run_post_ner(
                transcript_file=transcript_file,
                movie_dir=movie_dir,
                logger=logger,
                config=env_config
            )
            
            duration = time.time() - start
            
            # Create output directory
            post_ner_dir = movie_dir / 'post_ner'
            post_ner_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Post-NER directory: {post_ner_dir}")
            
            # Save corrected segments
            output_file = post_ner_dir / f'{movie_name}.corrected.json'
            
            output_data = {
                'segments': corrected_segments,
                'statistics': stats,
                'config': {
                    'model': env_config['model_name'],
                    'device': env_config['device'],
                    'entity_correction_enabled': env_config['entity_correction'],
                    'tmdb_matching_enabled': env_config['tmdb_matching'],
                    'confidence_threshold': env_config['confidence_threshold']
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.log_file_operation("Saved corrected segments", output_file, success=True)
            
            # Save text version
            txt_file = post_ner_dir / f'{movie_name}.corrected.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                for seg in corrected_segments:
                    speaker = seg.get('speaker', 'UNKNOWN')
                    text = seg.get('text', '').strip()
                    if text:
                        f.write(f"[{speaker}] {text}\n")
            
            logger.log_file_operation("Saved text version", txt_file, success=True)
            
            # Add to manifest
            manifest.add_output('corrected', output_file, 'Post-ASR NER corrected transcript')
            manifest.add_metadata('device', env_config['device'])
            manifest.add_metadata('model', env_config['model_name'])
            manifest.add_metadata('segments', stats['segments_processed'])
            manifest.add_metadata('corrections', stats['total_corrections'])
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
