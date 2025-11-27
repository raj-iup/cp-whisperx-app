#!/usr/bin/env python3
"""
Clean Existing Transcript - Remove Hallucinations

Utility to clean existing transcripts that already have hallucinations
"""

import sys
import json
from pathlib import Path

# Add scripts to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from hallucination_removal import HallucinationRemover
from shared.logger import PipelineLogger


def clean_job_transcript(job_path: Path, dry_run: bool = False):
    """
    Clean hallucinations from a specific job's transcript
    
    Args:
        job_path: Path to job directory
        dry_run: If True, only analyze without modifying
    """
    print(f"\n{'=' * 70}")
    print(f"Cleaning Job: {job_path}")
    print(f"{'=' * 70}\n")
    
    # Find segments file
    segments_file = None
    possible_locations = [
        job_path / "06_whisperx_asr" / "segments.json",
        job_path / "whisperx_asr" / "segments.json",
        job_path / "transcripts" / "segments.json",
    ]
    
    for loc in possible_locations:
        if loc.exists():
            segments_file = loc
            break
    
    if not segments_file:
        print(f"❌ Segments file not found in job: {job_path}")
        return False
    
    print(f"Found segments: {segments_file}")
    
    # Load segments
    try:
        with open(segments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load segments: {e}")
        return False
    
    # Extract segments
    if isinstance(data, dict):
        segments = data.get('segments', [])
        metadata = {k: v for k, v in data.items() if k != 'segments'}
    else:
        segments = data
        metadata = {}
    
    print(f"Loaded {len(segments)} segments\n")
    
    # Initialize remover
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("clean_transcript")
    
    remover = HallucinationRemover(
        loop_threshold=3,
        max_repeats=2,
        logger=None  # Use simple logging
    )
    
    # Process segments
    print("Analyzing for hallucinations...")
    cleaned_segments, stats = remover.process_segments(segments)
    
    # Display results
    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"Original segments: {stats['original_count']}")
    print(f"Cleaned segments: {stats['cleaned_count']}")
    print(f"Removed segments: {stats['removed_count']}")
    print(f"Loops detected: {stats['loops_detected']}")
    
    if stats['loops_removed']:
        print(f"\nDetected loops:")
        for start_idx, end_idx, text in stats['loops_removed']:
            count = end_idx - start_idx + 1
            print(f"  • '{text}' repeated {count} times (segments {start_idx}-{end_idx})")
    
    # Save cleaned version
    if not dry_run:
        # Backup original
        backup_file = segments_file.with_suffix('.json.backup')
        if not backup_file.exists():
            print(f"\nBacking up original to: {backup_file}")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save cleaned
        output_data = metadata.copy()
        output_data['segments'] = cleaned_segments
        output_data['hallucination_removal'] = stats
        
        print(f"Saving cleaned segments to: {segments_file}")
        with open(segments_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Regenerate transcript.txt
        transcript_file = job_path / "transcripts" / "transcript.txt"
        if transcript_file.exists():
            backup_txt = transcript_file.with_suffix('.txt.backup')
            if not backup_txt.exists():
                print(f"Backing up transcript to: {backup_txt}")
                transcript_file.rename(backup_txt)
            
            print(f"Regenerating transcript: {transcript_file}")
            with open(transcript_file, 'w', encoding='utf-8') as f:
                for seg in cleaned_segments:
                    text = seg.get('text', '').strip()
                    if text:
                        f.write(text + '\n')
        
        print(f"\n✅ Transcript cleaned successfully!")
    else:
        print(f"\n[DRY RUN] No files modified")
    
    print(f"{'=' * 70}\n")
    return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean hallucinations from existing transcripts"
    )
    parser.add_argument(
        'job_path',
        type=str,
        nargs='?',
        help='Path to job directory (default: latest job)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze without modifying files'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Clean all jobs in out/ directory'
    )
    
    args = parser.parse_args()
    
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  TRANSCRIPT HALLUCINATION CLEANER".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    if args.all:
        # Clean all jobs
        out_dir = PROJECT_ROOT / "out"
        if not out_dir.exists():
            print("\n❌ Output directory not found")
            return 1
        
        # Find all job directories
        jobs = []
        for year_dir in out_dir.iterdir():
            if not year_dir.is_dir() or year_dir.name.startswith('.'):
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    for user_dir in day_dir.iterdir():
                        if not user_dir.is_dir():
                            continue
                        for job_dir in user_dir.iterdir():
                            if job_dir.is_dir() and not job_dir.name.startswith('.'):
                                jobs.append(job_dir)
        
        if not jobs:
            print("\n❌ No jobs found in out/ directory")
            return 1
        
        print(f"\nFound {len(jobs)} job(s)")
        print(f"Dry run: {args.dry_run}")
        
        success_count = 0
        for job in jobs:
            if clean_job_transcript(job, args.dry_run):
                success_count += 1
        
        print(f"\n{'=' * 70}")
        print(f"Cleaned {success_count}/{len(jobs)} job(s)")
        print(f"{'=' * 70}\n")
        
    else:
        # Clean specific job or latest
        if args.job_path:
            job_path = Path(args.job_path)
        else:
            # Find latest job
            latest_link = PROJECT_ROOT / "out" / "LATEST_JOB"
            if latest_link.exists() and latest_link.is_symlink():
                job_path = latest_link.resolve()
            else:
                # Find most recent job
                out_dir = PROJECT_ROOT / "out"
                jobs = []
                for year_dir in out_dir.iterdir():
                    if not year_dir.is_dir() or year_dir.name.startswith('.'):
                        continue
                    for month_dir in year_dir.iterdir():
                        if not month_dir.is_dir():
                            continue
                        for day_dir in month_dir.iterdir():
                            if not day_dir.is_dir():
                                continue
                            for user_dir in day_dir.iterdir():
                                if not user_dir.is_dir():
                                    continue
                                for job_dir in user_dir.iterdir():
                                    if job_dir.is_dir() and not job_dir.name.startswith('.'):
                                        jobs.append(job_dir)
                
                if not jobs:
                    print("\n❌ No jobs found")
                    return 1
                
                # Sort by modification time
                jobs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                job_path = jobs[0]
        
        if not job_path.exists():
            print(f"\n❌ Job path not found: {job_path}")
            return 1
        
        print(f"\nDry run: {args.dry_run}")
        
        success = clean_job_transcript(job_path, args.dry_run)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
