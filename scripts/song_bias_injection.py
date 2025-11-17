#!/usr/bin/env python3
"""
song_bias_injection.py - Song-specific ASR Bias Correction Stage (NEW Stage 7)

Applies bias correction specifically for song lyrics, artist names, and titles.
This is a second pass after ASR to improve accuracy of musical content.

Architecture:
- Stage 6 (ASR): Runs with character name bias
- Stage 7 (This stage): Applies song-specific bias correction
- Stage 8 (Lyrics Detection): Detects which segments are lyrics
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from shared.stage_utils import StageIO
from shared.config import load_config
from bias_injection_core import BiasCorrector


def load_song_bias_terms(stage_io: StageIO, logger: PipelineLogger) -> List[str]:
    """
    Load song-specific bias terms from TMDB soundtrack data using centralized loader
    
    Args:
        stage_io: Stage I/O handler
        logger: Logger instance
        
    Returns:
        List of song-specific bias terms (titles, artists, composers)
    """
    try:
        # Use centralized bias registry
        from shared.bias_registry import BiasRegistry
        
        registry = BiasRegistry(stage_io.output_base, logger)
        bias_terms = registry.get_for_stage('song_bias_injection')
        
        if bias_terms:
            logger.info(f"Loaded {len(bias_terms)} song-specific bias terms from registry")
            return bias_terms
        
        # Fallback: check if TMDB data exists
        from shared.tmdb_loader import TMDBLoader
        tmdb_loader = TMDBLoader(stage_io.output_base, logger)
        tmdb_data = tmdb_loader.load()
        
        if tmdb_data.found and tmdb_data.soundtrack:
            logger.info(f"Found {len(tmdb_data.soundtrack)} songs in soundtrack")
            return bias_terms  # Will be empty but at least we tried
        
        # Add common Bollywood singers as last resort fallback
        logger.info("No soundtrack data, using common Bollywood artists as fallback")
        return [
            "Kumar Sanu", "Alka Yagnik", "Udit Narayan", "Anuradha Paudwal",
            "Sonu Nigam", "Shreya Ghoshal", "Arijit Singh", "Neha Kakkar",
            "Lata Mangeshkar", "Asha Bhosle", "Kishore Kumar", "Mohammed Rafi"
        ]
        
    except Exception as e:
        logger.error(f"Failed to load song bias terms: {e}")
        return []


def main():
    """Main entry point for song bias injection stage"""
    
    # Setup stage I/O
    stage_io = StageIO("song_bias_injection")
    
    # Setup logger
    log_file = stage_io.get_log_path()
    logger = PipelineLogger("song_bias_injection", log_file)
    
    logger.info("=" * 70)
    logger.info("SONG BIAS INJECTION STAGE - Lyrics & Artist Name Correction")
    logger.info("=" * 70)
    logger.info(f"Output base: {stage_io.output_base}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Load configuration
    config_path = stage_io.output_base / f".{stage_io.output_base.name}.env"
    if not config_path.exists():
        config_path = Path("config/.env.pipeline")
    
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)
    
    # Auto-detect if song bias should be enabled
    song_bias_enabled = getattr(config, 'song_bias_enabled', True)
    
    # Check TMDB data to auto-enable for Bollywood movies
    if song_bias_enabled:
        try:
            from shared.tmdb_loader import TMDBLoader
            tmdb_loader = TMDBLoader(stage_io.output_base, logger)
            
            # Auto-enable for Bollywood movies with soundtrack
            if tmdb_loader.should_enable_song_bias():
                logger.info("✓ Auto-enabled song bias (Bollywood movie with soundtrack detected)")
                song_bias_enabled = True
                
                # Log detection info
                tmdb_data = tmdb_loader.load()
                logger.info(f"  Movie: {tmdb_data.title} ({tmdb_data.year})")
                logger.info(f"  Genres: {', '.join(tmdb_data.genres[:3])}")
                logger.info(f"  Soundtrack: {len(tmdb_data.soundtrack)} songs")
            elif not tmdb_loader.load().found:
                logger.info("TMDB data not available - using config setting")
        except Exception as e:
            logger.warning(f"Could not auto-detect Bollywood movie: {e}")
    
    if not song_bias_enabled:
        logger.info("Song bias injection is disabled - skipping")
        # Copy ASR output as-is
        asr_data = stage_io.load_json("segments.json", from_stage="asr")
        stage_io.save_json(asr_data, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Load ASR segments
    logger.info("Loading ASR segments...")
    try:
        asr_data = stage_io.load_json("segments.json", from_stage="asr")
    except Exception as e:
        logger.error(f"Failed to load ASR segments: {e}")
        return 1
    
    # Extract segments
    if isinstance(asr_data, dict):
        segments = asr_data.get('segments', [])
    else:
        segments = asr_data
    
    logger.info(f"Loaded {len(segments)} segments from ASR")
    
    if not segments:
        logger.warning("No segments found in ASR output")
        stage_io.save_json(asr_data, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Load song-specific bias terms
    logger.info("Loading song bias terms...")
    song_bias_terms = load_song_bias_terms(stage_io, logger)
    
    if not song_bias_terms:
        logger.warning("No song bias terms found - skipping correction")
        # Copy ASR output as-is
        stage_io.save_json(asr_data, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Apply bias correction
    logger.info(f"Applying song bias correction with {len(song_bias_terms)} terms...")
    
    # Use lower fuzzy threshold for song titles (they're often transcribed incorrectly)
    # Lowered from 0.85 to 0.75 for better recall on song names/artists
    fuzzy_threshold = getattr(config, 'song_bias_fuzzy_threshold', 0.75)
    
    corrector = BiasCorrector(
        bias_terms=song_bias_terms,
        fuzzy_threshold=fuzzy_threshold,
        phonetic_threshold=0.80,  # Lower from 0.85 to 0.80 for better matching
        min_word_length=3,
        logger=logger
    )
    
    # Correct segments (batch processing)
    logger.info("Correcting segments...")
    corrected_segments, stats = corrector.correct_segments(segments)
    
    total_corrections = stats.get('total_corrections', 0)
    corrected_count = stats.get('corrected_segments', 0)
    
    logger.info(f"✓ Processed {len(corrected_segments)} segments")
    logger.info(f"✓ Corrected {corrected_count} segments with {total_corrections} changes")
    if stats.get('methods'):
        methods = stats['methods']
        logger.info(f"  Methods: exact={methods.get('exact', 0)}, fuzzy={methods.get('fuzzy', 0)}, "
                   f"phonetic={methods.get('phonetic', 0)}, context={methods.get('context', 0)}")
    
    # Prepare output data
    if isinstance(asr_data, dict):
        corrected_data = asr_data.copy()
        corrected_data['segments'] = corrected_segments
        corrected_data['song_bias_applied'] = True
        corrected_data['song_bias_terms_count'] = len(song_bias_terms)
        corrected_data['song_corrections_count'] = total_corrections
    else:
        corrected_data = corrected_segments
    
    # Save corrected data
    stage_io.save_json(corrected_data, "segments.json")
    
    # Save metadata
    metadata = {
        "status": "completed",
        "song_bias_terms": len(song_bias_terms),
        "corrections_applied": total_corrections,
        "fuzzy_threshold": fuzzy_threshold
    }
    stage_io.save_metadata(metadata)
    
    logger.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
