#!/usr/bin/env python3
"""
export_transcript.py - Export transcripts to multiple formats

Stage: 09_export_transcript (Stage 9)
Purpose: Export ASR transcript to various formats for downstream use

Supported formats:
- JSON: Full transcript with word-level timestamps (default from ASR)
- TXT: Plain text without timestamps
- SRT: SRT format with metadata (segment-level timing)
- VTT: WebVTT format (for web players)
- TSV: Tab-separated values (time, text)

Input: transcript.json from ASR stage
Output: Multiple transcript formats
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import timedelta

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


def format_timestamp_srt(seconds: float) -> str:
    """
    Format timestamp for SRT format (HH:MM:SS,mmm)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """
    Format timestamp for VTT format (HH:MM:SS.mmm)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def export_json(transcript_data: Dict[str, Any], output_path: Path, logger) -> bool:
    """
    Export to JSON format (pass-through, already in JSON)
    
    Args:
        transcript_data: Transcript dictionary
        output_path: Output file path
        logger: Logger instance
        
    Returns:
        True if successful
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Exported JSON: {output_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to export JSON: {e}")
        return False


def export_txt(transcript_data: Dict[str, Any], output_path: Path, logger) -> bool:
    """
    Export to plain text format (no timestamps)
    
    Args:
        transcript_data: Transcript dictionary
        output_path: Output file path
        logger: Logger instance
        
    Returns:
        True if successful
    """
    try:
        segments = transcript_data.get('segments', [])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                text = segment.get('text', '').strip()
                if text:
                    f.write(text + '\n')
        
        logger.info(f"✓ Exported TXT: {output_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to export TXT: {e}")
        return False


def export_srt(transcript_data: Dict[str, Any], output_path: Path, logger) -> bool:
    """
    Export to SRT format (SubRip)
    
    Args:
        transcript_data: Transcript dictionary
        output_path: Output file path
        logger: Logger instance
        
    Returns:
        True if successful
    """
    try:
        segments = transcript_data.get('segments', [])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, segment in enumerate(segments, 1):
                start = segment.get('start', 0.0)
                end = segment.get('end', start + 2.0)
                text = segment.get('text', '').strip()
                
                if not text:
                    continue
                
                # Write SRT entry
                f.write(f"{idx}\n")
                f.write(f"{format_timestamp_srt(start)} --> {format_timestamp_srt(end)}\n")
                f.write(f"{text}\n\n")
        
        logger.info(f"✓ Exported SRT: {output_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to export SRT: {e}")
        return False


def export_vtt(transcript_data: Dict[str, Any], output_path: Path, logger) -> bool:
    """
    Export to WebVTT format
    
    Args:
        transcript_data: Transcript dictionary
        output_path: Output file path
        logger: Logger instance
        
    Returns:
        True if successful
    """
    try:
        segments = transcript_data.get('segments', [])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for segment in segments:
                start = segment.get('start', 0.0)
                end = segment.get('end', start + 2.0)
                text = segment.get('text', '').strip()
                
                if not text:
                    continue
                
                # Write VTT entry
                f.write(f"{format_timestamp_vtt(start)} --> {format_timestamp_vtt(end)}\n")
                f.write(f"{text}\n\n")
        
        logger.info(f"✓ Exported VTT: {output_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to export VTT: {e}")
        return False


def export_tsv(transcript_data: Dict[str, Any], output_path: Path, logger) -> bool:
    """
    Export to TSV format (tab-separated values)
    
    Args:
        transcript_data: Transcript dictionary
        output_path: Output file path
        logger: Logger instance
        
    Returns:
        True if successful
    """
    try:
        segments = transcript_data.get('segments', [])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("start\tend\ttext\n")
            
            for segment in segments:
                start = segment.get('start', 0.0)
                end = segment.get('end', start + 2.0)
                text = segment.get('text', '').strip()
                
                if not text:
                    continue
                
                # Escape tabs and newlines in text
                text_escaped = text.replace('\t', ' ').replace('\n', ' ')
                f.write(f"{start:.3f}\t{end:.3f}\t{text_escaped}\n")
        
        logger.info(f"✓ Exported TSV: {output_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to export TSV: {e}")
        return False


def main():
    """
    Main entry point for transcript export stage
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Setup stage I/O
        stage_io = StageIO("export_transcript")
        logger = get_stage_logger("export_transcript", stage_io=stage_io)
        
        logger.info("=" * 70)
        logger.info("EXPORT TRANSCRIPT STAGE: Multi-format Export")
        logger.info("=" * 70)
        
        # Load config
        try:
            config = load_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return 1
        
        # Get input transcript
        transcript_file = stage_io.get_input_path("transcript.json", from_stage="asr")
        
        if not transcript_file.exists():
            logger.error(f"Transcript file not found: {transcript_file}")
            return 1
        
        logger.info(f"Input transcript: {transcript_file}")
        
        # Load transcript data
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load transcript: {e}")
            return 1
        
        # Get segments count
        segments_count = len(transcript_data.get('segments', []))
        logger.info(f"Loaded {segments_count} segments")
        
        if segments_count == 0:
            logger.warning("No segments found in transcript")
            return 1
        
        # Determine which formats to export (from config)
        export_formats = getattr(config, 'export_formats', ['json', 'txt', 'srt'])
        if isinstance(export_formats, str):
            export_formats = [f.strip() for f in export_formats.split(',')]
        
        logger.info(f"Export formats: {', '.join(export_formats)}")
        
        # Export to each format
        success_count = 0
        total_count = len(export_formats)
        
        exporters = {
            'json': export_json,
            'txt': export_txt,
            'srt': export_srt,
            'vtt': export_vtt,
            'tsv': export_tsv
        }
        
        for fmt in export_formats:
            fmt_lower = fmt.lower()
            if fmt_lower not in exporters:
                logger.warning(f"Unknown format '{fmt}', skipping")
                continue
            
            output_file = stage_io.get_output_path(f"transcript.{fmt_lower}")
            
            if exporters[fmt_lower](transcript_data, output_file, logger):
                success_count += 1
        
        # Summary
        logger.info("=" * 70)
        if success_count == total_count:
            logger.info(f"✓ Successfully exported {success_count}/{total_count} formats")
            logger.info("=" * 70)
            logger.info("EXPORT TRANSCRIPT STAGE COMPLETED")
            logger.info("=" * 70)
            return 0
        else:
            logger.warning(f"⚠ Exported {success_count}/{total_count} formats")
            logger.info("=" * 70)
            logger.info("EXPORT TRANSCRIPT STAGE COMPLETED WITH WARNINGS")
            logger.info("=" * 70)
            return 1 if success_count == 0 else 0
        
    except KeyboardInterrupt:
        logger.warning("✗ Export interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"✗ Export failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
