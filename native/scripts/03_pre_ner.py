#!/usr/bin/env python3
"""Stage 3: Pre-NER - Extract named entities before ASR"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest

def extract_entities(tmdb_data, device, logger):
    """Extract entities from TMDB data"""
    logger.info(f"Extracting entities on {device}")
    logger.debug(f"Processing TMDB data: {tmdb_data.get('title', 'Unknown')}")
    
    import time
    start = time.time()
    
    entities = {
        'persons': [],
        'locations': [],
        'titles': []
    }
    
    # Extract from TMDB data
    if 'cast' in tmdb_data:
        entities['persons'] = [p.get('name', '') for p in tmdb_data['cast'][:10]]
    
    duration = time.time() - start
    logger.log_processing("Entity extraction complete", duration)
    logger.log_metric("Person names extracted", len(entities['persons']))
    logger.log_metric("Locations extracted", len(entities['locations']))
    logger.log_metric("Titles extracted", len(entities['titles']))
    
    return entities

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--movie-dir', required=True)
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('pre-ner', movie_name)
    
    try:
        logger.log_stage_start("Pre-ASR Named Entity Recognition")
        
        # Use MPS if available
        device = get_device(prefer_mps=True, stage_name='pre-ner')
        logger.log_model_load("NER Model (placeholder)", device)
        
        with StageManifest('pre-ner', movie_dir, logger.logger) as manifest:
            # Load TMDB data
            tmdb_file = movie_dir / 'metadata' / 'tmdb_data.json'
            logger.debug(f"Loading TMDB data from: {tmdb_file}")
            
            with open(tmdb_file) as f:
                tmdb_data = json.load(f)
            
            # Extract entities
            entities = extract_entities(tmdb_data, device, logger)
            
            # Save entities
            entities_dir = movie_dir / 'entities'
            entities_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created entities directory: {entities_dir}")
            
            output_file = entities_dir / 'pre_ner.json'
            
            with open(output_file, 'w') as f:
                json.dump(entities, f, indent=2)
            
            logger.log_file_operation("Saved pre-NER entities", output_file, success=True)
            
            manifest.add_output('entities', output_file, 'Pre-ASR entities')
            manifest.add_metadata('device', device)
            manifest.add_metadata('person_count', len(entities['persons']))
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise

if __name__ == '__main__':
    main()
