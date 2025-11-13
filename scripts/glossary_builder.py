#!/usr/bin/env python3
"""
Glossary Builder stage: Build glossary from ASR output
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger

# Try to import MPS utils for future-proofing
try:
    from mps_utils import cleanup_mps_memory
    HAS_MPS_UTILS = True
except:
    HAS_MPS_UTILS = False

def main():
    # Initialize StageIO and logging
    stage_io = StageIO("glossary_builder")
    logger = get_stage_logger("glossary_builder", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("GLOSSARY BUILDER STAGE")
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
    
    # Check if glossary building is needed
    glossary_strategy = config.get('GLOSSARY_STRATEGY', 'none')
    logger.info(f"Glossary strategy: {glossary_strategy}")
    
    if glossary_strategy == 'none':
        logger.info("Glossary building disabled, skipping...")
        logger.info("=" * 60)
        return 0
    
    # Build glossary from ASR output using StageIO
    asr_file = stage_io.get_input_path("transcript.json", from_stage="asr")
    logger.info(f"Input ASR file: {asr_file}")
    
    if not asr_file.exists():
        logger.warning(f"ASR output not found: {asr_file}")
        logger.warning("Skipping glossary building (not critical)")
        return 0  # Not critical, continue pipeline
    
    # Read ASR output
    with open(asr_file, 'r', encoding='utf-8', errors='replace') as f:
        asr_data = json.load(f)
    
    # Extract unique words for glossary
    words = set()
    if isinstance(asr_data, dict) and 'segments' in asr_data:
        for segment in asr_data['segments']:
            if 'text' in segment:
                words.update(segment['text'].split())
    
    logger.info(f"Extracted {len(words)} unique terms")
    
    # Save glossary using StageIO
    glossary_data = {
        'strategy': glossary_strategy,
        'terms': sorted(list(words))
    }
    
    output_file = stage_io.save_json(glossary_data, "terms.json")
    logger.info(f"Saved glossary: {output_file}")
    
    # Save metadata
    metadata = {
        "status": "completed",
        "terms_count": len(words),
        "strategy": glossary_strategy,
        "stage": "glossary_builder",
        "stage_number": stage_io.stage_number,
        "timestamp": datetime.now().isoformat()
    }
    stage_io.save_json(metadata, "metadata.json")
    
    logger.info(f"✓ Glossary built: {len(words)} terms")
    logger.info(f"  Output directory: {stage_io.stage_dir}")
    logger.info("=" * 60)
    logger.info("GLOSSARY BUILDER STAGE COMPLETED")
    logger.info("=" * 60)
    
    # Cleanup memory (future-proofing for if ML models are added)
    if HAS_MPS_UTILS:
        cleanup_mps_memory()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())