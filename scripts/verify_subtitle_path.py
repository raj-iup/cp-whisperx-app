#!/usr/bin/env python3
"""
Subtitle Path Resolution Verification Script

Tests that the subtitle path fix correctly resolves subtitle file locations.
"""

from pathlib import Path
import sys

def get_subtitle_path(output_dir_path):
    """
    Replicate the subtitle path resolution logic from pipeline.py
    
    Args:
        output_dir_path: Path to job output directory
    
    Returns:
        str: Resolved subtitle file path
    """
    output_dir = Path(output_dir_path)
    job_id = output_dir.name
    subtitle_file = output_dir / "en_merged" / f"{job_id}.merged.srt"
    
    # Fallback to old location if new location doesn't exist
    if not subtitle_file.exists():
        subtitle_file = output_dir / "subtitles" / "subtitles.srt"
    
    return str(subtitle_file)

def verify_subtitle_path(job_dir):
    """
    Verify subtitle path resolution for a given job directory
    
    Args:
        job_dir: Path to job output directory
    
    Returns:
        bool: True if subtitle found, False otherwise
    """
    job_path = Path(job_dir)
    
    if not job_path.exists():
        print(f"✗ Job directory not found: {job_dir}")
        return False
    
    job_id = job_path.name
    subtitle_path = get_subtitle_path(str(job_path))
    subtitle_file = Path(subtitle_path)
    
    print(f"\nJob Directory: {job_path}")
    print(f"Job ID: {job_id}")
    print(f"Resolved Path: {subtitle_path}")
    
    if subtitle_file.exists():
        size = subtitle_file.stat().st_size
        print(f"✓ Subtitle found!")
        print(f"  Size: {size:,} bytes")
        print(f"  Location: {'en_merged/' if 'en_merged' in str(subtitle_file) else 'subtitles/'}")
        return True
    else:
        print(f"✗ Subtitle not found at resolved path")
        
        # Check both possible locations
        new_loc = job_path / "en_merged" / f"{job_id}.merged.srt"
        old_loc = job_path / "subtitles" / "subtitles.srt"
        
        print(f"\nChecking possible locations:")
        print(f"  New: {new_loc} - {'EXISTS' if new_loc.exists() else 'NOT FOUND'}")
        print(f"  Old: {old_loc} - {'EXISTS' if old_loc.exists() else 'NOT FOUND'}")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python verify_subtitle_path.py <job_directory>")
        print("\nExample:")
        print("  python verify_subtitle_path.py out/2025/11/08/1/20251108-0002")
        sys.exit(1)
    
    job_dir = sys.argv[1]
    
    print("=" * 70)
    print("SUBTITLE PATH RESOLUTION VERIFICATION")
    print("=" * 70)
    
    success = verify_subtitle_path(job_dir)
    
    print("\n" + "=" * 70)
    if success:
        print("RESULT: ✓ PASS - Subtitle path resolution working correctly")
    else:
        print("RESULT: ✗ FAIL - Subtitle not found")
    print("=" * 70)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
