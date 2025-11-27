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
from shared.config import load_config

# Try to import MPS utils for future-proofing
try:
    from mps_utils import cleanup_mps_memory
    HAS_MPS_UTILS = True
except:
    HAS_MPS_UTILS = False

def main():
    stage_io = None
    logger = None
    
    try:
        # Initialize StageIO with manifest tracking
        stage_io = StageIO("glossary_load", enable_manifest=True)
        logger = stage_io.get_stage_logger("INFO")
    
    logger.info("=" * 60)
    logger.info("GLOSSARY LOAD STAGE")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        stage_io.add_error(f"Config load failed: {e}", e)
        stage_io.finalize(status="failed")
        return 1
    
    # Check if glossary building is needed
    glossary_strategy = getattr(config, 'glossary_strategy', 'none')
    logger.info(f"Glossary strategy: {glossary_strategy}")
    
    # Track configuration
    stage_io.set_config({
        "glossary_strategy": glossary_strategy
    })
    
    if glossary_strategy == 'none':
        logger.info("Glossary building disabled, skipping...")
        logger.info("=" * 60)
        stage_io.finalize(status="skipped", reason="Strategy set to 'none'")
        return 0
    
    # Build glossary from ASR output using StageIO
    asr_file = stage_io.get_input_path("transcript.json", from_stage="asr")
    logger.info(f"Input ASR file: {asr_file}")
    
    if not asr_file.exists():
        logger.warning(f"ASR output not found: {asr_file}")
        logger.warning("Skipping glossary building (not critical)")
        stage_io.add_warning("ASR output not found")
        stage_io.finalize(status="skipped", reason="No ASR output")
        return 0  # Not critical, continue pipeline
    
    try:
        # Track input
        stage_io.track_input(asr_file, "transcript", format="json")
        
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
        
        # Track output
        stage_io.track_output(output_file, "glossary",
                             format="json",
                             terms_count=len(words),
                             strategy=glossary_strategy)
        
        # Save metadata
        metadata = {
            "status": "completed",
            "terms_count": len(words),
            "strategy": glossary_strategy,
            "stage": "glossary_builder",
            "stage_number": stage_io.stage_number,
            "timestamp": datetime.now().isoformat()
        }
        metadata_file = stage_io.save_json(metadata, "metadata.json")
        stage_io.track_intermediate(metadata_file, retained=True,
                                   reason="Stage metadata")
        
        # Finalize with success
        stage_io.finalize(status="success", terms_count=len(words))
        
        logger.info("=" * 60)
        logger.info("GLOSSARY LOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
        logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
        
        # Cleanup memory (future-proofing for if ML models are added)
        if HAS_MPS_UTILS:
            cleanup_mps_memory()
        
        return 0
        
    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"File not found: {e}")
            stage_io.finalize(status="failed", error=f"Missing file: {e}")
        return 1
    
    except IOError as e:
        if logger:
            logger.error(f"I/O error: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"I/O error: {e}")
            stage_io.finalize(status="failed", error=f"IO error: {e}")
        return 1
    
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"Invalid JSON in input: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"JSON decode error: {e}")
            stage_io.finalize(status="failed", error=f"Invalid JSON: {e}")
        return 1
    
    except KeyboardInterrupt:
        if logger:
            logger.warning("Interrupted by user")
        if stage_io:
            stage_io.add_error("User interrupted")
            stage_io.finalize(status="failed", error="User interrupted")
        return 130
    
    except Exception as e:
        if logger:
            logger.error(f"Glossary building failed: {e}", exc_info=True)
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        if stage_io:
            stage_io.add_error(f"Glossary build failed: {e}")
            stage_io.finalize(status="failed", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())