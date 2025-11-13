#!/usr/bin/env python3
"""
Reset pipeline stages to PENDING state to allow rerunning them.

Usage:
    python3 scripts/reset_stages.py --job 20251109-0004 --stages subtitle_gen mux finalize
    python3 scripts/reset_stages.py --job 20251109-0004 --stages subtitle_gen mux finalize --dry-run
"""
import json
import argparse
import sys
from pathlib import Path


def find_manifest(job_id: str) -> Path:
    """Find manifest file for a job."""
    if len(job_id) != 13 or job_id[8] != '-':
        raise ValueError(f"Invalid job ID format: {job_id} (expected: YYYYMMDD-NNNN)")
    
    year = job_id[0:4]
    month = job_id[4:6]
    day = job_id[6:8]
    
    # Search in new output structure
    date_dir = Path("out") / year / month / day
    if date_dir.exists():
        for user_dir in date_dir.iterdir():
            if user_dir.is_dir():
                manifest_file = user_dir / job_id / "manifest.json"
                if manifest_file.exists():
                    return manifest_file
    
    raise FileNotFoundError(f"Manifest not found for job: {job_id}")


def reset_stages(job_id: str, stages: list, dry_run: bool = False):
    """Reset specified stages to PENDING state."""
    manifest_path = find_manifest(job_id)
    
    print(f"Job: {job_id}")
    print(f"Manifest: {manifest_path}")
    print()
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Get current state
    completed = data.get("pipeline", {}).get("completed_stages", [])
    failed = data.get("pipeline", {}).get("failed_stages", [])
    
    print("Current state:")
    print(f"  Completed stages: {', '.join(completed) if completed else 'None'}")
    print(f"  Failed stages: {', '.join(failed) if failed else 'None'}")
    print()
    
    # Determine stages to reset
    stages_to_reset = []
    for stage in stages:
        if stage in completed or stage in failed or stage in data.get("stages", {}):
            stages_to_reset.append(stage)
        else:
            print(f"⚠️  Stage '{stage}' not found in manifest - will still be available to run")
    
    if not stages_to_reset and not stages:
        print("No stages to reset.")
        return
    
    print(f"Stages to reset: {', '.join(stages)}")
    print()
    
    if dry_run:
        print("DRY RUN - no changes made")
        print()
        print("Would remove from completed_stages:")
        for stage in stages:
            if stage in completed:
                print(f"  - {stage}")
        print()
        print("Would remove from failed_stages:")
        for stage in stages:
            if stage in failed:
                print(f"  - {stage}")
        print()
        print("Would reset stage data:")
        for stage in stages:
            if stage in data.get("stages", {}):
                print(f"  - {stage}: {data['stages'][stage].get('status', 'unknown')}")
        return
    
    # Reset stages
    modified = False
    
    # Remove from completed_stages
    for stage in stages:
        if stage in completed:
            completed.remove(stage)
            modified = True
            print(f"✓ Removed '{stage}' from completed_stages")
    
    # Remove from failed_stages
    for stage in stages:
        if stage in failed:
            failed.remove(stage)
            modified = True
            print(f"✓ Removed '{stage}' from failed_stages")
    
    # Reset stage data to pending
    for stage in stages:
        if stage in data.get("stages", {}):
            old_status = data["stages"][stage].get("status", "unknown")
            # Mark as pending/incomplete
            data["stages"][stage]["completed"] = False
            data["stages"][stage]["status"] = "pending"
            modified = True
            print(f"✓ Reset '{stage}' stage data (was: {old_status})")
    
    if not modified:
        print("⚠️  No changes needed - stages are already pending")
        return
    
    # Update pipeline status if needed
    if data.get("pipeline", {}).get("status") == "completed" and stages_to_reset:
        data["pipeline"]["status"] = "running"
        print("✓ Updated pipeline status to 'running'")
    
    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print(f"✓ Manifest updated: {manifest_path}")
    print()
    print("You can now run:")
    print(f"  python3 scripts/pipeline.py --job {job_id} --stages {' '.join(stages)}")


def main():
    parser = argparse.ArgumentParser(
        description="Reset pipeline stages to PENDING state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reset specific stages
  python3 scripts/reset_stages.py --job 20251109-0004 --stages subtitle_gen mux finalize
  
  # Dry run to see what would change
  python3 scripts/reset_stages.py --job 20251109-0004 --stages subtitle_gen mux --dry-run
  
  # Reset a single stage
  python3 scripts/reset_stages.py --job 20251109-0004 --stages asr
        """
    )
    parser.add_argument("--job", required=True, help="Job ID (e.g., 20251109-0004)")
    parser.add_argument("--stages", nargs="+", required=True, help="Stages to reset")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying")
    
    args = parser.parse_args()
    
    try:
        reset_stages(args.job, args.stages, args.dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
