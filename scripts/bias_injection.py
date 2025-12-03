#!/usr/bin/env python3
"""
bias_injection.py - Bias Correction Stage (Stage 9: Post-Processing)

Applies fuzzy/phonetic matching corrections to fix remaining errors after:
- Stage 6: ASR with character name bias
- Stage 7: Song-specific bias correction
- Stage 8: Lyrics detection

This is the final correction pass using multiple matching methods:
- Exact matching (case-insensitive)
- Fuzzy matching (Levenshtein distance)
- Phonetic matching (Metaphone/Soundex)
- Context-aware temporal windows

Previously called "bias_injection", now serves as "bias_correction" (Stage 9).
"""

# Standard library
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
from bias_injection_core import BiasCorrector, ContextAwareBiasCorrector

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


def load_bias_terms(stage_io: StageIO, logger: PipelineLogger) -> List[str]:
    """
    Load bias terms from TMDB and pre-NER stages
    
    Args:
        stage_io: Stage I/O handler
        logger: Logger instance
        
    Returns:
        List of bias terms
    """
    bias_terms = []
    
    # Try loading from TMDB enrichment
    tmdb_file = stage_io.output_base / "02_tmdb" / "enrichment.json"
    if tmdb_file.exists():
        try:
            with open(tmdb_file, 'r', encoding='utf-8') as f:
                tmdb_data = json.load(f)
            
            # Extract cast and crew names
            cast = tmdb_data.get('cast', [])
            crew = tmdb_data.get('crew', [])
            
            # Handle both string arrays and dict arrays
            for person in cast:
                if isinstance(person, str):
                    name = person
                else:
                    name = person.get('name', '')
                if name:
                    bias_terms.append(name)
            
            for person in crew:
                if isinstance(person, str):
                    name = person
                else:
                    name = person.get('name', '')
                if name:
                    bias_terms.append(name)
            
            logger.info(f"Loaded {len(bias_terms)} terms from TMDB")
        except Exception as e:
            logger.warning(f"Failed to load TMDB data: {e}")
    
    # Try loading from pre-NER
    prener_file = stage_io.output_base / "03_pre_ner" / "entities.json"
    if prener_file.exists():
        try:
            with open(prener_file, 'r', encoding='utf-8') as f:
                prener_data = json.load(f)
            
            entities = prener_data.get('entities', [])
            for entity in entities:
                text = entity.get('text', '')
                if text and text not in bias_terms:
                    bias_terms.append(text)
            
            logger.info(f"Added {len(entities)} terms from pre-NER")
        except Exception as e:
            logger.warning(f"Failed to load pre-NER data: {e}")
    
    # Remove duplicates, preserve order
    seen = set()
    unique_terms = []
    for term in bias_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    
    logger.info(f"Total unique bias terms: {len(unique_terms)}")
    
    return unique_terms


def load_bias_windows(stage_io: StageIO, logger: PipelineLogger) -> List[Dict]:
    """
    Load temporal bias windows if available
    
    Args:
        stage_io: Stage I/O handler
        logger: Logger instance
        
    Returns:
        List of bias windows
    """
    windows_file = stage_io.output_base / "06_asr" / "bias_windows.json"
    
    if not windows_file.exists():
        # Try alternative location
        windows_file = stage_io.output_base / "06_asr" / "bias_windows" / "windows.json"
    
    if not windows_file.exists():
        logger.debug("No bias windows found (optional)")
        return []
    
    try:
        with open(windows_file, 'r', encoding='utf-8') as f:
            windows = json.load(f)
        
        if isinstance(windows, list):
            logger.info(f"Loaded {len(windows)} bias windows")
            return windows
        elif isinstance(windows, dict) and 'windows' in windows:
            window_list = windows['windows']
            logger.info(f"Loaded {len(window_list)} bias windows")
            return window_list
    except Exception as e:
        logger.warning(f"Failed to load bias windows: {e}")
    
    return []


def should_run_bias_injection(device: str, enabled: str, logger: PipelineLogger) -> bool:
    """
    Determine if bias injection should run based on device and config
    
    Args:
        device: Device type (mps, cpu, cuda)
        enabled: Configuration value (auto, true, false)
        logger: Logger instance
        
    Returns:
        True if should run bias injection
    """
    device_lower = device.lower()
    enabled_lower = enabled.lower()
    
    if enabled_lower == 'false':
        logger.info("Bias injection: Disabled by configuration")
        return False
    
    if enabled_lower == 'true':
        logger.info(f"Bias injection: Force-enabled (device={device_lower})")
        return True
    
    # Auto mode: Enable for MPS, optional for CPU/CUDA
    if enabled_lower == 'auto':
        if device_lower == 'mps':
            logger.info("Bias injection: Enabled (MPS - no bias in ASR)")
            return True
        else:
            logger.info(f"Bias injection: Running light pass (device={device_lower} already has bias)")
            return True  # Always run, but log that ASR already had bias
    
    # Default: run for MPS
    if device_lower == 'mps':
        logger.info("Bias injection: Enabled (MPS default)")
        return True
    
    logger.info(f"Bias injection: Running additional pass (device={device_lower})")
    return True


def main(stage_name: Optional[str] = None):
    """Main entry point for bias correction stage (Stage 9: Post-processing)
    
    This stage applies fuzzy/phonetic matching corrections to fix any remaining
    errors after ASR, song bias, and lyrics detection.
    
    Args:
        stage_name: Optional stage name (defaults to "bias_correction")
    """
    
    # Use bias_correction as the stage name
    if stage_name is None:
        stage_name = "bias_correction"
    
    # Setup stage I/O
    stage_io = StageIO(stage_name)
    
    # Setup logger
    log_file = stage_io.get_log_path()
    logger = PipelineLogger(stage_name, log_file)
    
    logger.info("=" * 70)
    logger.info("BIAS CORRECTION STAGE - Post-Processing Fuzzy/Phonetic Correction")
    logger.info("=" * 70)
    logger.info(f"Output base: {stage_io.output_base}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Load configuration
    config_path = stage_io.output_base / f".{stage_io.output_base.name}.env"
    if not config_path.exists():
        config_path = Path("config/.env.pipeline")
    
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)
    
    # Get device and settings
    device = getattr(config, 'whisperx_device', getattr(config, 'device', 'cpu'))
    enabled = getattr(config, 'bias_injection_enabled', 'auto')
    fuzzy_threshold = getattr(config, 'bias_fuzzy_threshold', 0.85)
    phonetic_threshold = getattr(config, 'bias_phonetic_threshold', 0.90)
    min_word_length = getattr(config, 'bias_min_word_length', 3)
    use_context = getattr(config, 'bias_use_context_windows', True)
    
    logger.info(f"Device: {device}")
    logger.info(f"Configuration:")
    logger.info(f"  Enabled: {enabled}")
    logger.info(f"  Fuzzy threshold: {fuzzy_threshold}")
    logger.info(f"  Phonetic threshold: {phonetic_threshold}")
    logger.info(f"  Min word length: {min_word_length}")
    logger.info(f"  Context windows: {use_context}")
    
    # Check if should run
    if not should_run_bias_injection(device, enabled, logger):
        logger.info("Skipping bias correction stage")
        # Copy lyrics detection output as-is
        try:
            segments = stage_io.load_json("segments.json", from_stage="lyrics_detection")
            stage_io.save_json(segments, "segments.json")
        except Exception as e:
            logger.error(f"Failed to copy segments: {e}", exc_info=True)
            return 1
        logger.info("=" * 70)
        return 0
    
    # Load segments from lyrics detection stage
    logger.info("Loading segments from lyrics detection stage...")
    try:
        asr_data = stage_io.load_json("segments.json", from_stage="lyrics_detection")
    except Exception as e:
        logger.error(f"Failed to load segments: {e}", exc_info=True)
        return 1
    
    # Handle both formats: list of segments or dict with 'segments' key
    if isinstance(asr_data, list):
        segments = asr_data
    elif isinstance(asr_data, dict):
        segments = asr_data.get('segments', [])
    else:
        logger.error(f"Unexpected data format: {type(asr_data, exc_info=True)}")
        return 1
    
    logger.info(f"Loaded {len(segments)} segments")
    
    if not segments:
        logger.warning("No segments found")
        # Save empty output (preserve original format)
        output_data = segments if isinstance(asr_data, list) else asr_data
        stage_io.save_json(output_data, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Load bias terms (character names, places, etc.)
    logger.info("Loading bias terms for correction...")
    bias_terms = load_bias_terms(stage_io, logger)
    
    if not bias_terms:
        logger.warning("No bias terms found - skipping correction")
        # Copy input as-is
        stage_io.save_json(asr_data, "segments.json")
        logger.info("=" * 70)
        return 0
    
    # Load bias windows (optional - for context-aware correction)
    bias_windows = []
    if use_context:
        logger.info("Loading bias windows for context-aware correction...")
        bias_windows = load_bias_windows(stage_io, logger)
    
    # Initialize corrector
    logger.info("Initializing bias corrector...")
    
    if bias_windows and use_context:
        corrector = ContextAwareBiasCorrector(
            bias_terms=bias_terms,
            bias_windows=bias_windows,
            fuzzy_threshold=fuzzy_threshold,
            phonetic_threshold=phonetic_threshold,
            min_word_length=min_word_length,
            logger=logger
        )
        logger.info("  Using context-aware corrector")
    else:
        corrector = BiasCorrector(
            bias_terms=bias_terms,
            fuzzy_threshold=fuzzy_threshold,
            phonetic_threshold=phonetic_threshold,
            min_word_length=min_word_length,
            logger=logger
        )
        logger.info("  Using standard corrector")
    
    # Apply corrections
    logger.info("Applying bias corrections...")
    logger.info(f"  Processing {len(segments)} segments...")
    
    try:
        corrected_segments, stats = corrector.correct_segments(segments)
    except Exception as e:
        logger.error(f"Bias correction failed: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc(, exc_info=True))
        return 1
    
    # Log statistics
    logger.info("=" * 70)
    logger.info("CORRECTION STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Total segments:       {stats['total_segments']}")
    logger.info(f"Segments corrected:   {stats['corrected_segments']}")
    logger.info(f"Total corrections:    {stats['total_corrections']}")
    
    if stats['total_corrections'] > 0:
        logger.info(f"Correction rate:      {100 * stats['corrected_segments'] / stats['total_segments']:.1f}%")
        logger.info("")
        logger.info("Method breakdown:")
        for method, count in stats['methods'].items():
            if count > 0:
                pct = 100 * count / stats['total_corrections']
                logger.info(f"  {method:12s}: {count:5d} ({pct:5.1f}%)")
    else:
        logger.info("No corrections needed")
    
    # Save corrected output
    logger.info("=" * 70)
    logger.info("Saving corrected output...")
    
    # Preserve original format: list or dict
    if isinstance(asr_data, list):
        # Original was a list of segments, keep it as a list
        corrected_data = corrected_segments
    else:
        # Original was a dict, merge with corrected segments
        corrected_data = {
            **asr_data,
            'segments': corrected_segments,
            'bias_correction': {
                'applied': True,
                'device': device,
                'stats': stats,
                'config': {
                    'fuzzy_threshold': fuzzy_threshold,
                    'phonetic_threshold': phonetic_threshold,
                    'min_word_length': min_word_length,
                    'use_context': use_context
                }
            }
        }
    
    stage_io.save_json(corrected_data, "segments.json")
    logger.info(f"  Saved: {stage_io.stage_dir / 'segments.json'}")
    
    # Save metadata
    metadata = {
        'status': 'completed',
        'device': device,
        'bias_terms_count': len(bias_terms),
        'bias_windows_count': len(bias_windows),
        **stats
    }
    stage_io.save_metadata(metadata)
    logger.info(f"  Saved: {stage_io.stage_dir / 'metadata.json'}")
    
    logger.info("=" * 70)
    logger.info("BIAS INJECTION STAGE COMPLETED")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
