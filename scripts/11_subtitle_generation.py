#!/usr/bin/env python3
"""
Subtitle Generation Stage (11_subtitle_generation)

Generates SRT subtitle files from translated transcripts.

Input: Translated transcript segments (from 10_translation)
Output: SRT subtitle files for all target languages
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


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segments: List[Dict], output_path: Path, language: str = "en") -> int:
    """
    Generate SRT subtitle file from segments.
    
    Args:
        segments: List of segment dicts with start, end, text
        output_path: Output SRT file path
        language: Language code for filename
        
    Returns:
        Number of subtitles generated
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            # Skip removed or empty segments
            if segment.get("removed", False):
                continue
            
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            # Segment number
            f.write(f"{i}\n")
            
            # Timestamps
            start = format_timestamp_srt(segment.get('start', 0))
            end = format_timestamp_srt(segment.get('end', 0))
            f.write(f"{start} --> {end}\n")
            
            # Text
            f.write(f"{text}\n")
            
            # Blank line between segments
            f.write("\n")
    
    return i


def run_stage(job_dir: Path, stage_name: str = "11_subtitle_generation") -> int:
    """
    Subtitle Generation Stage
    
    Generates SRT subtitle files from translated transcripts.
    
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
        logger.info("STAGE: Subtitle Generation")
        logger.info("=" * 80)
        
        # Load configuration
        config = load_config()
        subtitle_enabled = config.get("STAGE_09_SUBTITLE_ENABLED", "true").lower() == "true"
        
        if not subtitle_enabled:
            logger.info("Subtitle generation disabled in configuration, skipping")
            io.finalize(status="success")
            return 0
        
        # Get target languages
        target_lang_str = config.get("TARGET_LANGUAGE", "en")
        if target_lang_str is None:
            target_lang_str = "en"
        target_languages = target_lang_str.split(",")
        logger.info(f"Target languages: {target_languages}")
        
        # Find translation output
        translation_dir = io.output_base / "08_translation"
        
        if not translation_dir.exists():
            logger.warning(f"Translation directory not found: {translation_dir}")
            logger.info("Looking for cleaned transcript instead")
            
            # Try to find cleaned or original transcript
            input_file = None
            for dir_name in ["07_hallucination_removal", "06_lyrics_detection", "04_asr"]:
                candidate_dir = io.output_base / dir_name
                if candidate_dir.exists():
                    for pattern in ["transcript_cleaned.json", "transcript_with_lyrics.json", "transcript.json"]:
                        candidate = candidate_dir / pattern
                        if candidate.exists():
                            input_file = candidate
                            break
                    if input_file:
                        break
            
            if not input_file:
                logger.error("No transcript found for subtitle generation")
                io.finalize(status="failed")
                return 1
            
            logger.info(f"Using transcript: {input_file}")
            io.track_input(input_file, "transcript")
            
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            segments = data.get("segments", [])
            if not segments:
                segments = data if isinstance(data, list) else []
            
            # Generate subtitle for original language
            srt_file = io.stage_dir / "subtitles.srt"
            count = generate_srt(segments, srt_file)
            io.track_output(srt_file, "subtitle")
            
            logger.info(f"Generated {count} subtitles: {srt_file}")
            
        else:
            # Find translated transcript files
            translation_files = list(translation_dir.glob("transcript_*.json"))
            
            if not translation_files:
                logger.warning(f"No translation files found in {translation_dir}")
                logger.info("Creating empty subtitle")
                
                srt_file = io.stage_dir / "subtitles.srt"
                with open(srt_file, 'w') as f:
                    f.write("")
                io.track_output(srt_file, "subtitle")
                
                io.finalize(status="success")
                return 0
            
            logger.info(f"Found {len(translation_files)} translation file(s)")
            
            # Generate SRT for each translation
            total_subtitles = 0
            for trans_file in translation_files:
                logger.info(f"Processing: {trans_file.name}")
                io.track_input(trans_file, "translation")
                
                with open(trans_file, 'r') as f:
                    data = json.load(f)
                
                segments = data.get("segments", [])
                if not segments:
                    segments = data if isinstance(data, list) else []
                
                # Extract language from filename (transcript_en.json -> en)
                lang = trans_file.stem.split("_")[-1] if "_" in trans_file.stem else "en"
                
                # Generate SRT
                srt_file = io.stage_dir / f"subtitles_{lang}.srt"
                count = generate_srt(segments, srt_file, lang)
                io.track_output(srt_file, "subtitle")
                
                logger.info(f"Generated {count} subtitles for {lang}: {srt_file.name}")
                total_subtitles += count
        
        # Summary
        srt_files = list(io.stage_dir.glob("*.srt"))
        logger.info("=" * 80)
        logger.info("Subtitle Generation Complete")
        logger.info(f"  SRT files generated: {len(srt_files)}")
        for srt_file in srt_files:
            logger.info(f"    - {srt_file.name}")
        logger.info("=" * 80)
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Subtitle generation stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Subtitle Generation Stage")
    parser.add_argument("--job-dir", type=Path, required=True, help="Job directory")
    parser.add_argument("--stage-name", default="11_subtitle_generation", help="Stage name")
    
    args = parser.parse_args()
    
    exit_code = run_stage(args.job_dir, args.stage_name)
    sys.exit(exit_code)
