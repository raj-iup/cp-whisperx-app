#!/usr/bin/env python3
"""
Glossary Applier Stage (12b) - Apply glossary to translations

Applies unified glossary to translation output with:
- Context-aware term selection
- Film-specific overrides
- Usage tracking for learning
"""

# Standard library
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.glossary_unified import load_glossary

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


def detect_context(segment: dict) -> str:
    """
    Detect context from segment
    
    Args:
        segment: Segment dictionary with text
    
    Returns:
        Context string (formal/casual/emotional/aggressive)
    """
    text = segment.get('text', '').lower()
    
    # Check for formal indicators
    formal_markers = ['sir', 'madam', 'please', 'kindly', 'respectfully']
    if any(marker in text for marker in formal_markers):
        return 'formal'
    
    # Check for casual indicators
    casual_markers = ['dude', 'bro', 'man', 'hey', 'cool']
    if any(marker in text for marker in casual_markers):
        return 'casual'
    
    # Check for emotional indicators
    emotional_markers = ['love', 'heart', 'cry', 'sad', 'happy']
    if any(marker in text for marker in emotional_markers):
        return 'emotional'
    
    # Check for aggressive indicators
    aggressive_markers = ['fight', 'kill', 'angry', 'hate']
    if any(marker in text for marker in aggressive_markers):
        return 'aggressive'
    
    # Default to general
    return 'general'


def apply_glossary_to_segments(
    segments: list,
    glossary,
    logger
) -> tuple:
    """
    Apply glossary to all segments
    
    Args:
        segments: List of segment dictionaries
        glossary: UnifiedGlossary instance
        logger: Logger instance
    
    Returns:
        Tuple of (modified_segments, statistics)
    """
    modified_segments = []
    stats = {
        'total_segments': len(segments),
        'modified_segments': 0,
        'total_terms_applied': 0,
        'contexts_detected': {},
        'film_terms_used': 0
    }
    
    for segment in segments:
        original_text = segment.get('text', '')
        
        if not original_text:
            modified_segments.append(segment)
            continue
        
        # Detect context
        context = detect_context(segment)
        stats['contexts_detected'][context] = stats['contexts_detected'].get(context, 0) + 1
        
        # Apply glossary
        modified_text = glossary.apply(original_text, context=context)
        
        # Check if text was modified
        if modified_text != original_text:
            segment['text'] = modified_text
            segment['glossary_applied'] = True
            segment['glossary_context'] = context
            stats['modified_segments'] += 1
        
        modified_segments.append(segment)
    
    # Get glossary statistics
    glossary_stats = glossary.get_statistics()
    stats['total_terms_applied'] = glossary_stats['terms_applied']
    stats['film_terms_used'] = glossary_stats['film_specific']
    
    return modified_segments, stats


def main():
    """Main glossary applier stage"""
    
    # Initialize StageIO and logging
    stage_io = StageIO("glossary_applier")
    logger = get_stage_logger("glossary_applier", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("STAGE 12b: GLOSSARY APPLIER")
    logger.info("=" * 60)
    
    # Load configuration
    config_path_env = os.environ.get('CONFIG_PATH')
    config = {}
    
    if config_path_env:
        logger.debug(f"Loading configuration from: {config_path_env}")
        config_path = Path(config_path_env)
        
        with open(config_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
    
    # Check if glossary is enabled
    glossary_enabled = config.get('GLOSSARY_ENABLED', 'true').lower() == 'true'
    
    if not glossary_enabled:
        logger.info("Glossary disabled, skipping...")
        logger.info("=" * 60)
        return 0
    
    # Get film information
    film_title = config.get('FILM_TITLE', '')
    film_year = config.get('FILM_YEAR', '')
    film_name = f"{film_title}_{film_year}" if film_title and film_year else None
    
    logger.info(f"Film: {film_title} ({film_year})")
    
    # Load glossary
    glossary_path = PROJECT_ROOT / config.get('GLOSSARY_PATH', 'glossary/unified_glossary.tsv')
    
    if not glossary_path.exists():
        logger.warning(f"Glossary not found: {glossary_path}")
        logger.warning("Skipping glossary application")
        return 0
    
    logger.info(f"Loading glossary: {glossary_path}")
    glossary = load_glossary(glossary_path, film_name, logger)
    
    glossary_stats = glossary.get_statistics()
    logger.info(f"Loaded glossary: {glossary_stats['total_terms']} terms")
    
    if glossary_stats['film_specific'] > 0:
        logger.info(f"  Film-specific terms: {glossary_stats['film_specific']}")
    
    # Get input from translation stage
    translation_file = stage_io.get_input_path(
        "translated_segments.json",
        from_stage="second_pass_translation"
    )
    
    if not translation_file.exists():
        logger.error(f"Translation output not found: {translation_file}")
        return 1
    
    logger.info(f"Input: {translation_file}")
    
    # Load translated segments
    with open(translation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get('segments', [])
    logger.info(f"Processing {len(segments)} segments")
    
    # Apply glossary
    logger.info("Applying glossary...")
    modified_segments, stats = apply_glossary_to_segments(segments, glossary, logger)
    
    # Update data
    data['segments'] = modified_segments
    data['glossary_applied'] = True
    data['glossary_statistics'] = stats
    
    # Save output
    output_file = stage_io.get_output_path("glossary_applied.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Output: {output_file}")
    
    # Report statistics
    logger.info("=" * 60)
    logger.info("GLOSSARY APPLICATION STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total segments: {stats['total_segments']}")
    logger.info(f"Modified segments: {stats['modified_segments']} ({stats['modified_segments']/stats['total_segments']*100:.1f}%)")
    logger.info(f"Total terms applied: {stats['total_terms_applied']}")
    logger.info(f"Film-specific terms used: {stats['film_terms_used']}")
    
    logger.info("\nContexts detected:")
    for context, count in sorted(stats['contexts_detected'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {context}: {count}")
    
    # Save learned terms
    if glossary_stats['terms_applied'] > 0:
        learned_path = PROJECT_ROOT / "glossary" / "glossary_learned" / f"{film_name}_learned.tsv"
        glossary.save_learned(learned_path)
        logger.info(f"\nSaved learned terms: {learned_path}")
    
    logger.info("=" * 60)
    logger.info("✓ Glossary application complete")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
