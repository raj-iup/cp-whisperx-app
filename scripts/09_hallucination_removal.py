#!/usr/bin/env python3
"""
Hallucination Removal Stage (09_hallucination_removal)

Removes ASR hallucinations (repeated phrases, artifacts, nonsense).
MANDATORY for subtitle workflow - cannot be disabled.

Input: ASR transcript with lyrics markers (from 08_lyrics_detection)
Output: Cleaned transcript with hallucinations removed
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import re

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local
from shared.stage_utils import StageIO
from shared.config import load_config
from shared.logger import get_logger

logger = get_logger(__name__)


def is_hallucination(text: str) -> bool:
    """
    Detect if segment is likely a hallucination.
    
    Args:
        text: Segment text
        
    Returns:
        True if likely hallucination
    """
    if not text or len(text.strip()) == 0:
        return True
    
    text_lower = text.lower().strip()
    
    # Common hallucination patterns
    hallucination_patterns = [
        r'^thanks for watching',
        r'^thank you for watching',
        r'^subscribe',
        r'^like and subscribe',
        r'^please subscribe',
        r'^don\'t forget to',
        r'^visit our website',
        r'^www\.',
        r'^http',
        r'^\[music\]',
        r'^\[applause\]',
        r'^\[laughter\]',
        r'^\[.*\]$',  # Pure annotation markers
    ]
    
    for pattern in hallucination_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Very short segments (often artifacts)
    if len(text_lower) < 3:
        return True
    
    # Excessive repetition (same word 5+ times)
    words = text_lower.split()
    if len(words) >= 5:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        if any(count >= len(words) * 0.6 for count in word_counts.values()):
            return True
    
    return False


def run_stage(job_dir: Path, stage_name: str = "09_hallucination_removal") -> int:
    """
    Hallucination Removal Stage
    
    Removes ASR hallucinations from transcript.
    
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
        logger.info("STAGE: Hallucination Removal")
        logger.info("=" * 80)
        
        # Load configuration
        config = load_config()
        removal_enabled = config.get("STAGE_09_HALLUCINATION_ENABLED", "true").lower() == "true"
        
        if not removal_enabled:
            logger.warning("Hallucination removal is MANDATORY for subtitle workflow")
            logger.info("Continuing with hallucination removal despite config setting")
            # Don't skip - this is mandatory for subtitle workflow
        
        # Find input transcript (prefer lyrics detection output)
        input_file = None
        
        # Try lyrics detection output first
        lyrics_dir = io.output_base / "08_lyrics_detection"
        if lyrics_dir.exists():
            lyrics_file = lyrics_dir / "transcript_with_lyrics.json"
            if lyrics_file.exists():
                input_file = lyrics_file
        
        # Fall back to ASR output
        if not input_file:
            asr_dir = io.output_base / "04_asr"
            for pattern in ["transcript.json", "whisperx_output.json", "asr_output.json"]:
                candidate = asr_dir / pattern
                if candidate.exists():
                    input_file = candidate
                    break
        
        if not input_file:
            logger.warning("No transcript found")
            logger.info("Creating empty cleaned transcript")
            
            # Create empty output
            output_file = io.stage_dir / "transcript_cleaned.json"
            with open(output_file, 'w') as f:
                json.dump({"segments": []}, f, indent=2)
            
            io.track_output(output_file, "cleaned")
            io.finalize(status="success")
            return 0
        
        logger.info(f"Loading transcript: {input_file}")
        io.track_input(input_file, "transcript")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        segments = data.get("segments", [])
        if not segments:
            segments = data if isinstance(data, list) else []
        
        logger.info(f"Processing {len(segments)} segments for hallucination removal")
        
        # Remove hallucinations
        cleaned_segments = []
        removed_count = 0
        
        for segment in segments:
            text = segment.get("text", "")
            
            # Skip lyrics (they're legitimate even if repetitive)
            is_lyrics = segment.get("is_lyrics", False)
            
            if not is_lyrics and is_hallucination(text):
                segment["removed"] = True
                segment["reason"] = "hallucination"
                removed_count += 1
                logger.debug(f"Removed hallucination: '{text[:50]}'")
            else:
                segment["removed"] = False
                cleaned_segments.append(segment)
        
        # Save cleaned transcript
        output_data = {
            "segments": cleaned_segments,
            "removed_segments": [s for s in segments if s.get("removed", False)],
            "metadata": {
                "original_segments": len(segments),
                "cleaned_segments": len(cleaned_segments),
                "removed_segments": removed_count,
                "stage": stage_name
            }
        }
        
        output_file = io.stage_dir / "transcript_cleaned.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        io.track_output(output_file, "cleaned")
        
        logger.info(f"Created cleaned transcript: {output_file}")
        
        # Summary
        logger.info("=" * 80)
        logger.info("Hallucination Removal Complete")
        logger.info(f"  Original segments: {len(segments)}")
        logger.info(f"  Cleaned segments: {len(cleaned_segments)}")
        logger.info(f"  Removed segments: {removed_count}")
        logger.info(f"  Removal rate: {removed_count/len(segments)*100:.1f}%")
        logger.info("=" * 80)
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Hallucination removal stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hallucination Removal Stage")
    parser.add_argument("--job-dir", type=Path, required=True, help="Job directory")
    parser.add_argument("--stage-name", default="07_hallucination_removal", help="Stage name")
    
    args = parser.parse_args()
    
    exit_code = run_stage(args.job_dir, args.stage_name)
    sys.exit(exit_code)
