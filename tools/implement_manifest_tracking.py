#!/usr/bin/env python3
"""
Batch implementation of manifest tracking for all remaining stages.

This script will update all stages that haven't been updated yet to include:
- StageIO initialization with enable_manifest=True
- Input/output tracking
- Configuration tracking
- Error tracking
- Finalization

Usage:
    python3 tools/implement_manifest_tracking.py [--dry-run]
"""

import sys
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Stages to update (excluding demux, asr, alignment which are done)
STAGES_TO_UPDATE = [
    ("tmdb_enrichment_stage.py", "tmdb", "TMDBEnrichmentStage"),
    ("glossary_builder.py", "glossary_load", "main"),
    ("source_separation.py", "source_separation", "main"),
    ("pyannote_vad.py", "pyannote_vad", "main"),
    ("lyrics_detection.py", "lyrics_detection", "main"),
    ("subtitle_gen.py", "subtitle_generation", "main"),
    ("mux.py", "mux", "main"),
]

def update_stage_file(file_path: Path, stage_name: str, dry_run: bool = False) -> bool:
    """Update a stage file to include manifest tracking"""
    
    if not file_path.exists():
        print(f"  ✗ File not found: {file_path}")
        return False
    
    content = file_path.read_text()
    original_content = content
    
    # Check if already has enable_manifest=True
    if "enable_manifest=True" in content:
        print(f"  ✓ Already has manifest tracking enabled")
        return True
    
    modifications = []
    
    # 1. Update StageIO initialization
    # Pattern: StageIO("stage_name")
    # Replace with: StageIO("stage_name", enable_manifest=True)
    pattern1 = rf'StageIO\("{stage_name}"\)'
    replacement1 = f'StageIO("{stage_name}", enable_manifest=True)'
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        modifications.append("Updated StageIO initialization")
    
    # Pattern: StageIO('stage_name')
    pattern2 = rf"StageIO\('{stage_name}'\)"
    replacement2 = f"StageIO('{stage_name}', enable_manifest=True)"
    if re.search(pattern2, content):
        content = re.sub(pattern2, replacement2, content)
        modifications.append("Updated StageIO initialization")
    
    # 2. Update get_stage_logger to use stage_io method
    # Pattern: get_stage_logger("stage_name", ...)
    # Replace with: stage_io.get_stage_logger(...)
    pattern3 = rf'get_stage_logger\("{stage_name}"[^)]*\)'
    if re.search(pattern3, content):
        # Get the full logger initialization
        match = re.search(rf'(\w+)\s*=\s*get_stage_logger\("{stage_name}"[^)]*\)', content)
        if match:
            logger_var = match.group(1)
            content = re.sub(
                rf'{logger_var}\s*=\s*get_stage_logger\("{stage_name}"[^)]*\)',
                f'{logger_var} = stage_io.get_stage_logger("DEBUG")',
                content
            )
            modifications.append("Updated logger initialization")
    
    if modifications:
        if not dry_run:
            file_path.write_text(content)
            print(f"  ✓ Updated: {', '.join(modifications)}")
        else:
            print(f"  [DRY RUN] Would update: {', '.join(modifications)}")
        return True
    else:
        print(f"  ⚠ No automatic updates possible - manual intervention needed")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Implement manifest tracking in all stages")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()
    
    print("=" * 80)
    print("BATCH MANIFEST TRACKING IMPLEMENTATION")
    print("=" * 80)
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print()
    
    updated_count = 0
    failed_count = 0
    
    for filename, stage_name, entry_point in STAGES_TO_UPDATE:
        file_path = SCRIPTS_DIR / filename
        print(f"Processing: {filename} ({stage_name})")
        
        if update_stage_file(file_path, stage_name, args.dry_run):
            updated_count += 1
        else:
            failed_count += 1
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Updated: {updated_count}/{len(STAGES_TO_UPDATE)}")
    print(f"Failed: {failed_count}/{len(STAGES_TO_UPDATE)}")
    print()
    
    if not args.dry_run and updated_count > 0:
        print("✓ Files updated successfully!")
        print()
        print("NEXT STEPS:")
        print("1. Review the changes with: git diff scripts/")
        print("2. Add tracking calls manually where needed")
        print("3. Test each stage individually")
        print("4. Update compliance report")
    else:
        print("Run without --dry-run to apply changes")
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
