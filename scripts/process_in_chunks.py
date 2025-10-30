#!/usr/bin/env python3
"""Process long videos in chunks to avoid OOM."""
import subprocess
import sys
from pathlib import Path

def process_chunks(input_file, chunk_minutes=20):
    """Process video in chunks."""
    input_path = Path(input_file)
    
    # Get duration
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_path)
    ], capture_output=True, text=True, check=True)
    
    total_seconds = float(result.stdout.strip())
    chunk_seconds = chunk_minutes * 60
    
    print(f"Total duration: {total_seconds/60:.1f} minutes")
    print(f"Chunk size: {chunk_minutes} minutes")
    
    # Calculate chunks
    num_chunks = int(total_seconds / chunk_seconds) + 1
    print(f"Processing in {num_chunks} chunks...")
    
    chunk_dir = Path("in/chunks")
    chunk_dir.mkdir(exist_ok=True)
    
    # Split into chunks
    for i in range(num_chunks):
        start = i * chunk_seconds
        chunk_name = f"{input_path.stem}_chunk_{i+1:02d}.mp4"
        chunk_path = chunk_dir / chunk_name
        
        print(f"\nChunk {i+1}/{num_chunks}: Creating {chunk_name}...")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start),
            "-i", str(input_path),
            "-t", str(chunk_seconds),
            "-c", "copy",
            str(chunk_path)
        ], check=True, capture_output=True)
        
        print(f"  Processing chunk {i+1}...")
        subprocess.run([
            "python", "run_pipeline.py",
            "-i", str(chunk_path),
            "--infer-tmdb-from-filename",
            "--two-pass-merge"
        ], check=True)
    
    print(f"\n✅ All {num_chunks} chunks processed!")
    print(f"Output chunks in: out/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_in_chunks.py <input_file> [chunk_minutes]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    chunk_minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    process_chunks(input_file, chunk_minutes)
