#!/usr/bin/env python3
"""
Subtitle Generation stage: Generate subtitle files from transcript
"""
import sys
import os
import json
from pathlib import Path
from datetime import timedelta, datetime

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO

def format_timestamp(seconds):
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    # Get output directory from environment or command line
    output_dir_env = os.environ.get('OUTPUT_DIR')
    if output_dir_env:
        output_dir = Path(output_dir_env)
    elif len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        print("ERROR: No output directory specified", file=sys.stderr)
        return 1
    
    # Initialize StageIO
    stage_io = StageIO("subtitle_gen", output_base=output_dir)
    
    # Read transcript using StageIO
    transcript_file = stage_io.get_input_path("transcript.json", from_stage="asr")
    
    if not transcript_file.exists():
        print(f"ERROR: Transcript not found: {transcript_file}", file=sys.stderr)
        return 1
    
    with open(transcript_file, 'r', encoding='utf-8', errors='replace') as f:
        transcript = json.load(f)
    
    # Generate SRT file using StageIO
    srt_file = stage_io.get_output_path("subtitles.srt")
    
    subtitle_count = 0
    with open(srt_file, 'w', encoding='utf-8') as f:
        if isinstance(transcript, dict) and 'segments' in transcript:
            for i, segment in enumerate(transcript['segments'], 1):
                start = segment.get('start', 0)
                end = segment.get('end', start + 1)
                text = segment.get('text', '').strip()
                
                if text:
                    f.write(f"{i}\n")
                    f.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
                    f.write(f"{text}\n\n")
                    subtitle_count += 1
    
    # Save metadata
    metadata = {
        "status": "completed",
        "subtitle_count": subtitle_count,
        "format": "srt",
        "stage": "subtitle_gen",
        "stage_number": stage_io.stage_number,
        "timestamp": datetime.now().isoformat()
    }
    stage_io.save_json(metadata, "metadata.json")
    
    print(f"✓ Subtitles generated: {srt_file}")
    print(f"  Subtitle count: {subtitle_count}")
    print(f"  Output directory: {stage_io.stage_dir}")
    
    # Update manifest
    manifest_file = output_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8', errors='replace') as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    manifest.setdefault('stages', {})['subtitle_gen'] = {
        'status': 'completed',
        'subtitle_file': str(srt_file)
    }
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
