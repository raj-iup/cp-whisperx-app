#!/usr/bin/env python3
"""
Lyrics Detection Stage (08_lyrics_detection)

Detects lyrics/song sections in ASR transcript to avoid translating them.
MANDATORY for subtitle workflow - cannot be disabled.

Input: ASR transcript with segments (from 07_alignment)
Output: Annotated transcript with lyrics markers
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


def detect_lyrics_simple(text: str) -> bool:
    """
    Simple lyrics detection heuristic.
    
    Args:
        text: Segment text
        
    Returns:
        True if likely lyrics
    """
    # Simple heuristics for lyrics detection
    lyrics_patterns = [
        'la la la',
        'na na na',
        'ho ho ho',
        'sha la la',
        'doo doo doo',
        'oh oh oh',
        'yeah yeah yeah',
    ]
    
    text_lower = text.lower()
    
    # Check for repetitive patterns
    if any(pattern in text_lower for pattern in lyrics_patterns):
        return True
    
    # Check for high repetition
    words = text_lower.split()
    if len(words) > 3:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # If any word repeats 3+ times in short segment, likely lyrics
        if any(count >= 3 for count in word_counts.values()):
            return True
    
    return False


def run_stage(job_dir: Path, stage_name: str = "08_lyrics_detection") -> int:
    """
    Lyrics Detection Stage
    
    Detects and marks lyrics sections in ASR transcript.
    
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
        logger.info("STAGE: Lyrics Detection")
        logger.info("=" * 80)
        
        # Load configuration
        config = load_config()
        lyrics_enabled = config.get("STAGE_08_LYRICS_ENABLED", "true").lower() == "true"
        
        if not lyrics_enabled:
            logger.warning("Lyrics detection is MANDATORY for subtitle workflow")
            logger.info("Continuing with lyrics detection despite config setting")
            # Don't skip - this is mandatory for subtitle workflow
        
        # Find ASR transcript (or NER output if available)
        input_file = None
        
        # Try NER output first
        ner_dir = io.output_base / "05_ner"
        if ner_dir.exists():
            ner_file = ner_dir / "ner_entities.json"
            if ner_file.exists():
                input_file = ner_file
        
        # Fall back to ASR output
        if not input_file:
            asr_dir = io.output_base / "04_asr"
            for pattern in ["transcript.json", "whisperx_output.json", "asr_output.json"]:
                candidate = asr_dir / pattern
                if candidate.exists():
                    input_file = candidate
                    break
        
        if not input_file:
            logger.warning("No ASR/NER transcript found")
            logger.info("Creating empty lyrics detection output")
            
            # Create empty output
            output_file = io.stage_dir / "transcript_with_lyrics.json"
            with open(output_file, 'w') as f:
                json.dump({"segments": []}, f, indent=2)
            
            io.track_output(output_file, "lyrics")
            io.finalize(status="success")
            return 0
        
        logger.info(f"Loading transcript: {input_file}")
        io.track_input(input_file, "transcript")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        segments = data.get("segments", [])
        if not segments:
            segments = data if isinstance(data, list) else []
        
        logger.info(f"Processing {len(segments)} segments for lyrics detection")
        
        # Detect lyrics in each segment
        lyrics_count = 0
        for segment in segments:
            text = segment.get("text", "")
            is_lyrics = detect_lyrics_simple(text)
            segment["is_lyrics"] = is_lyrics
            
            if is_lyrics:
                lyrics_count += 1
        
        # Save annotated transcript
        output_data = {
            "segments": segments,
            "metadata": {
                "total_segments": len(segments),
                "lyrics_segments": lyrics_count,
                "stage": stage_name
            }
        }
        
        output_file = io.stage_dir / "transcript_with_lyrics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        io.track_output(output_file, "lyrics")
        
        logger.info(f"Created annotated transcript: {output_file}")
        
        # Summary
        logger.info("=" * 80)
        logger.info("Lyrics Detection Complete")
        logger.info(f"  Total segments: {len(segments)}")
        logger.info(f"  Lyrics segments: {lyrics_count}")
        logger.info(f"  Lyrics percentage: {lyrics_count/len(segments)*100:.1f}%")
        logger.info("=" * 80)
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Lyrics detection stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Lyrics Detection Stage")
    parser.add_argument("--job-dir", type=Path, required=True, help="Job directory")
    parser.add_argument("--stage-name", default="06_lyrics_detection", help="Stage name")
    
    args = parser.parse_args()
    
    exit_code = run_stage(args.job_dir, args.stage_name)
    sys.exit(exit_code)
