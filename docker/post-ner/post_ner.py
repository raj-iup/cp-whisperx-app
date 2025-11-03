#!/usr/bin/env python3
"""
Post-ASR NER container - Entity correction & enrichment

Workflow: Stage 8 (per workflow-arch.txt)
Input: diarization/*.diarized.json, pre_ner/entities.json, TMDB metadata
Output: post_ner/*.corrected.json with entity corrections
"""
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from rapidfuzz import fuzz, process

# Setup paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/shared')

from scripts.ner_extraction import NERProcessor
from logger import PipelineLogger


def load_tmdb_entities(movie_dir: Path, logger: PipelineLogger) -> List[str]:
    """Load entity names from TMDB metadata"""
    entities = []
    
    # Check for TMDB data
    tmdb_file = movie_dir / "metadata" / "tmdb.json"
    if tmdb_file.exists():
        try:
            with open(tmdb_file) as f:
                tmdb_data = json.load(f)
                
            # Extract cast names
            cast = tmdb_data.get("cast", [])
            entities.extend([c.get("name") for c in cast if c.get("name")])
            
            # Extract crew names
            crew = tmdb_data.get("crew", [])
            entities.extend([c.get("name") for c in crew if c.get("name")])
            
            logger.info(f"Loaded {len(entities)} entities from TMDB")
        except Exception as e:
            logger.warning(f"Failed to load TMDB data: {e}")
    
    return entities


def load_pre_ner_entities(movie_dir: Path, logger: PipelineLogger) -> List[str]:
    """Load entities from Pre-ASR NER"""
    entities = []
    
    pre_ner_file = movie_dir / "pre_ner" / "entities.json"
    if pre_ner_file.exists():
        try:
            with open(pre_ner_file) as f:
                data = json.load(f)
            entities = data.get("entities", [])
            logger.info(f"Loaded {len(entities)} entities from Pre-NER")
        except Exception as e:
            logger.warning(f"Failed to load Pre-NER data: {e}")
    
    return entities


def correct_entity_spelling(
    entity_text: str,
    reference_entities: List[str],
    threshold: int = 85
) -> Optional[str]:
    """
    Correct entity spelling using fuzzy matching
    
    Args:
        entity_text: Extracted entity text
        reference_entities: List of reference entity names (TMDB, Pre-NER)
        threshold: Minimum fuzzy match score (0-100)
    
    Returns:
        Corrected entity text or None if no match
    """
    if not reference_entities:
        return None
    
    # Find best match
    result = process.extractOne(
        entity_text,
        reference_entities,
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        return result[0]
    
    return None


def correct_segments(
    segments: List[Dict],
    reference_entities: List[str],
    model_name: str,
    device: str,
    threshold: float,
    logger: PipelineLogger
) -> List[Dict]:
    """
    Run NER on segments and correct entity spellings
    
    Args:
        segments: Diarized transcript segments
        reference_entities: List of reference entities from TMDB/Pre-NER
        model_name: spaCy NER model name
        device: Device to run on
        threshold: Confidence threshold for fuzzy matching (0-100)
        logger: Logger instance
    
    Returns:
        Corrected segments with entity annotations
    """
    logger.info("Running NER on transcript segments...")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Device: {device}")
    logger.info(f"  Threshold: {threshold}")
    
    # Initialize NER processor
    ner_processor = NERProcessor(
        model_name=model_name,
        device=device,
        logger=logger
    )
    ner_processor.load_model()
    
    corrected_segments = []
    corrections_made = 0
    
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            corrected_segments.append(segment)
            continue
        
        # Extract entities from segment text
        entities = ner_processor.extract_entities_from_text(text)
        
        # Correct entity spellings
        corrected_entities = []
        for entity in entities:
            entity_text = entity.get("text", "")
            corrected_text = correct_entity_spelling(
                entity_text,
                reference_entities,
                threshold=int(threshold)  # Convert to int for rapidfuzz
            )
            
            if corrected_text and corrected_text != entity_text:
                # Replace in text
                text = text.replace(entity_text, corrected_text)
                entity["corrected_text"] = corrected_text
                entity["original_text"] = entity_text
                corrections_made += 1
            
            corrected_entities.append(entity)
        
        # Update segment
        new_segment = segment.copy()
        new_segment["text"] = text
        new_segment["entities"] = corrected_entities
        corrected_segments.append(new_segment)
    
    logger.info(f"Entity corrections made: {corrections_made}")
    return corrected_segments


def main():
    if len(sys.argv) < 2:
        print("Usage: post_ner.py <movie_dir>")
        sys.exit(1)
    
    movie_dir = Path(sys.argv[1])
    
    # Load config
    try:
        from config import load_config
        config = load_config()
        log_level = config.log_level.upper() if hasattr(config, 'log_level') else "INFO"
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Setup logger
    logger = PipelineLogger("post-ner", log_level=log_level)
    logger.info(f"Starting Post-ASR NER for: {movie_dir}")
    
    # Get configuration parameters
    model_name = config.get('post_ner_model', 'en_core_web_trf')
    device = config.get('post_ner_device', 'cpu')
    entity_correction = config.get('post_ner_entity_correction', True)
    tmdb_matching = config.get('post_ner_tmdb_matching', True)
    confidence_threshold = config.get('post_ner_confidence_threshold', 0.8)
    
    # Convert threshold to 0-100 scale for rapidfuzz
    threshold = confidence_threshold * 100
    
    logger.info(f"Configuration:")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Device: {device}")
    logger.info(f"  Entity correction: {entity_correction}")
    logger.info(f"  TMDB matching: {tmdb_matching}")
    logger.info(f"  Confidence threshold: {confidence_threshold} ({threshold:.0f}%)")
    
    # Find ASR transcript with speaker labels (from Stage 7)
    asr_files = list(movie_dir.glob("asr/*.asr.json"))
    if not asr_files:
        logger.error("No ASR transcript found")
        sys.exit(1)
    asr_file = asr_files[0]
    
    logger.info(f"ASR transcript: {asr_file}")
    
    # Load ASR segments (with speaker labels from diarization)
    with open(asr_file) as f:
        asr_data = json.load(f)
    
    # Handle both formats
    if isinstance(asr_data, dict):
        segments = asr_data.get("segments", [])
    elif isinstance(asr_data, list):
        segments = asr_data
    else:
        logger.error("Unknown ASR format")
        sys.exit(1)
    
    logger.info(f"Loaded {len(segments)} segments")
    speakers_with_labels = sum(1 for seg in segments if seg.get("speaker"))
    logger.info(f"Segments with speaker labels: {speakers_with_labels}/{len(segments)}")
    
    # Load reference entities based on config
    reference_entities = []
    
    if tmdb_matching:
        tmdb_entities = load_tmdb_entities(movie_dir, logger)
        reference_entities.extend(tmdb_entities)
    else:
        logger.info("TMDB matching disabled")
    
    pre_ner_entities = load_pre_ner_entities(movie_dir, logger)
    reference_entities.extend(pre_ner_entities)
    
    # Combine and deduplicate
    reference_entities = list(set(reference_entities))
    logger.info(f"Total reference entities: {len(reference_entities)}")
    
    # Check if entity correction is enabled
    if not entity_correction:
        logger.info("Entity correction disabled - saving original segments")
        corrected_segments = segments
    else:
        # Run entity correction
        try:
            corrected_segments = correct_segments(
                segments,
                reference_entities,
                model_name,
                device,
                threshold,
                logger
            )
        except Exception as e:
            logger.error(f"Entity correction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    # Save results
    try:
        output_dir = movie_dir / "post_ner"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"{movie_dir.name}.corrected.json"
        
        # Add metadata
        output_data = {
            "segments": corrected_segments,
            "config": {
                "model": model_name,
                "device": device,
                "entity_correction_enabled": entity_correction,
                "tmdb_matching_enabled": tmdb_matching,
                "confidence_threshold": confidence_threshold,
                "reference_entities_count": len(reference_entities)
            }
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Post-ASR NER complete: {output_file}")
        
        # Also save as text
        txt_file = output_dir / f"{movie_dir.name}.corrected.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for seg in corrected_segments:
                speaker = seg.get("speaker", "UNKNOWN")
                text = seg.get("text", "").strip()
                if text:
                    f.write(f"[{speaker}] {text}\n")
        
        logger.info(f"✓ Saved text version: {txt_file}")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Post-ASR NER failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
