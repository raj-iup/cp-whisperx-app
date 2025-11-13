#!/usr/bin/env python3
"""
Mux stage: Combine video with subtitles
"""
import sys
import os
import subprocess
from pathlib import Path
import json

def main():
    # Load configuration from environment or command-line arguments
    config_path = os.environ.get('CONFIG_PATH')
    if config_path:
        config_path = Path(config_path)
    elif len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    else:
        config_path = Path("config/.env.pipeline")
    
    output_dir_env = os.environ.get('OUTPUT_DIR')
    if output_dir_env:
        output_dir = Path(output_dir_env)
    elif len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path("out")
    
    # Read config
    with open(config_path, 'r', encoding='utf-8', errors='replace') as f:
        config = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"')
    
    input_file = config.get('IN_ROOT', config.get('INPUT_MEDIA', ''))
    if not input_file or not Path(input_file).exists():
        print(f"ERROR: Input media not found: {input_file}", file=sys.stderr)
        return 1
    
    # Check for subtitle file - try multiple locations
    subtitle_file = output_dir / "subtitles" / "subtitles.srt"
    if not subtitle_file.exists():
        subtitle_file = output_dir / "subtitles.srt"
    
    if not subtitle_file.exists():
        print(f"ERROR: Subtitle file not found: {subtitle_file}", file=sys.stderr)
        return 1
    
    # Output video file
    output_file = output_dir / "output.mkv"
    
    # Mux video with subtitles using ffmpeg
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-i", str(subtitle_file),
        "-c", "copy",  # Copy streams without re-encoding
        "-c:s", "srt",  # Subtitle codec
        "-metadata:s:s:0", "language=eng",
        "-y",  # Overwrite
        str(output_file)
    ]
    
    print(f"Muxing video with subtitles: {output_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed: {result.stderr}", file=sys.stderr)
        return 1
    
    print(f"✓ Video muxed: {output_file}")
    
    # Update manifest
    manifest_file = output_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8', errors='replace') as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    manifest.setdefault('stages', {})['mux'] = {
        'status': 'completed',
        'output_file': str(output_file)
    }
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
