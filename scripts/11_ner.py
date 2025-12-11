#!/usr/bin/env python3
"""
NER Stage (05_ner) - EXPERIMENTAL

Named Entity Recognition for improving translation quality.
Extracts person names, organizations, and locations from ASR transcript.

AD-006 Note: This experimental stage uses system config only.
No job-specific parameters currently supported.

Input: ASR transcript with segments
Output: NER annotations, entity frequency table
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local
from shared.stage_utils import StageIO
from shared.config import load_config
from shared.logger import get_logger

logger = get_logger(__name__)


def run_stage(job_dir: Path, stage_name: str = "05_ner") -> int:
    """
    NER Stage
    
    Extracts named entities from ASR transcript.
    
    Args:
        job_dir: Job directory
        stage_name: Stage name for logging
        
    Returns:
        0 on success, 1 on failure
    """
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        logger.info("=" * 80)
        logger.info("STAGE: Named Entity Recognition (NER)")
        logger.info("=" * 80)
        
        # Load configuration
        config = load_config()
        ner_enabled = config.get("STAGE_05_NER_ENABLED", "true").lower() == "true"
        
        if not ner_enabled:
            logger.info("NER stage disabled in configuration, skipping")
            io.finalize(status="success")
            return 0
        
        # Find ASR transcript
        asr_dir = io.output_base / "04_asr"
        transcript_file = None
        
        for pattern in ["transcript.json", "whisperx_output.json", "asr_output.json"]:
            candidate = asr_dir / pattern
            if candidate.exists():
                transcript_file = candidate
                break
        
        if not transcript_file:
            logger.warning(f"No ASR transcript found in {asr_dir}")
            logger.info("Creating empty NER output")
            
            # Create empty output
            ner_file = io.stage_dir / "ner_entities.json"
            with open(ner_file, 'w') as f:
                json.dump({"entities": [], "segments": []}, f, indent=2)
            
            io.track_output(ner_file, "ner")
            io.finalize(status="success")
            return 0
        
        logger.info(f"Loading ASR transcript: {transcript_file}")
        io.track_input(transcript_file, "transcript")
        
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        
        segments = transcript_data.get("segments", [])
        if not segments:
            segments = transcript_data if isinstance(transcript_data, list) else []
        
        logger.info(f"Found {len(segments)} segments to process")
        
        # For now, create placeholder NER output
        # Full NER implementation would use spaCy here
        logger.info("NER processing: Creating placeholder output")
        logger.info("(Full NER implementation requires spaCy model)")
        
        ner_output = {
            "entities": [],
            "segments": segments,
            "metadata": {
                "total_segments": len(segments),
                "ner_model": "placeholder",
                "stage": stage_name
            }
        }
        
        # Save NER output
        ner_file = io.stage_dir / "ner_entities.json"
        with open(ner_file, 'w', encoding='utf-8') as f:
            json.dump(ner_output, f, indent=2, ensure_ascii=False)
        io.track_output(ner_file, "ner")
        
        logger.info(f"Created NER output: {ner_file}")
        
        # Summary
        logger.info("=" * 80)
        logger.info("NER Stage Complete")
        logger.info(f"  Segments processed: {len(segments)}")
        logger.info(f"  Entities extracted: {len(ner_output['entities'])}")
        logger.info("=" * 80)
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"NER stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NER Stage")
    parser.add_argument("--job-dir", type=Path, required=True, help="Job directory")
    parser.add_argument("--stage-name", default="05_ner", help="Stage name")
    
    args = parser.parse_args()
    
    exit_code = run_stage(args.job_dir, args.stage_name)
    sys.exit(exit_code)
