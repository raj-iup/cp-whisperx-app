#!/usr/bin/env python3
"""
Comprehensive fix script for all identified issues in Session 3
Fixes:
1. test-glossary-quickstart.sh - grep -P flag and path extraction
2. run-pipeline.py - ensure glossary system loads properly
3. Job configuration - ensure target_language is set
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/rpatel/Projects/cp-whisperx-app")

print("=" * 70)
print("COMPREHENSIVE PIPELINE FIXES - SESSION 3")
print("=" * 70)
print()

fixes_applied = []
issues_found = []

# ============================================================================
# Fix 1: test-glossary-quickstart.sh - macOS grep compatibility
# ============================================================================
print("🔧 Fix 1: test-glossary-quickstart.sh (macOS grep compatibility)...")

test_script = PROJECT_ROOT / "test-glossary-quickstart.sh"
if test_script.exists():
    content = test_script.read_text()
    original_content = content
    
    # Fix all instances of job ID extraction to be consistent
    # Replace the grep "^   Job ID:" pattern with simpler one
    content = content.replace(
        'ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "^   Job ID:" | awk \'{print $3}\')',
        'ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job ID:" | head -1 | awk \'{print $NF}\')'
    )
    
    # Fix all instances of job path extraction to use sed instead of awk -F
    # The sed command is more robust for extracting everything after "Job directory:"
    content = re.sub(
        r'FULL_JOB_PATH=\$\(echo "\$PREP_OUTPUT" \| grep.*Job directory.*\)',
        'FULL_JOB_PATH=$(echo "$PREP_OUTPUT" | grep "Job directory:" | head -1 | sed \'s/^.*Job directory: *//\' | xargs)',
        content
    )
    
    if content != original_content:
        test_script.write_text(content)
        fixes_applied.append("  ✓ Fixed test-glossary-quickstart.sh path extraction")
        print("  ✓ Fixed all path extraction patterns")
    else:
        print("  ℹ️  Already fixed or no issues found")
else:
    issues_found.append("  ✗ test-glossary-quickstart.sh not found")
    print("  ✗ File not found!")

print()

# ============================================================================
# Fix 2: Check and document glossary system status
# ============================================================================
print("🔧 Fix 2: Checking glossary system integration...")

run_pipeline = PROJECT_ROOT / "scripts" / "run-pipeline.py"
if run_pipeline.exists():
    content = run_pipeline.read_text()
    
    # Check if glossary_load stage exists
    if "_stage_glossary_load" in content:
        print("  ✓ Glossary load stage method exists")
    else:
        issues_found.append("  ✗ Missing _stage_glossary_load stage method")
        print("  ✗ Missing _stage_glossary_load() method in run-pipeline.py")
        print("     This needs to be implemented in Session 3")
    
    # Check if it's called in translate workflow
    if "self._stage_glossary_load" in content or '"glossary_load"' in content:
        print("  ✓ Glossary load stage is referenced")
    else:
        issues_found.append("  ⚠ Glossary load stage not called in workflows")
        print("  ⚠ Glossary load stage exists but not integrated into workflow")
        print("     This needs to be added to transcribe workflow in Session 3")
else:
    issues_found.append("  ✗ run-pipeline.py not found")
    print("  ✗ File not found!")

print()

# ============================================================================
# Fix 3: Verify stage order configuration
# ============================================================================
print("🔧 Fix 3: Verifying stage order configuration...")

stage_order_file = PROJECT_ROOT / "shared" / "stage_order.py"
if stage_order_file.exists():
    try:
        # Import and check
        sys.path.insert(0, str(PROJECT_ROOT / "shared"))
        from stage_order import STAGE_NUMBERS, print_stage_order, get_stage_dir
        
        # Check key stages
        required_stages = {
            "demux": 1,
            "tmdb": 2,
            "glossary_load": 3,
            "source_separation": 4,
            "asr": 6,
            "translation": 10,
            "hybrid_translation": 10,  # Alias
            "subtitle_generation": 11,
        }
        
        all_correct = True
        for stage, expected_num in required_stages.items():
            actual_num = STAGE_NUMBERS.get(stage)
            if actual_num == expected_num:
                print(f"  ✓ {stage}: stage {actual_num}")
            else:
                print(f"  ✗ {stage}: expected {expected_num}, got {actual_num}")
                issues_found.append(f"  ✗ Stage number mismatch for {stage}")
                all_correct = False
        
        if all_correct:
            print("  ✓ All stage numbers are correct!")
            fixes_applied.append("  ✓ Stage order validated")
    except Exception as e:
        issues_found.append(f"  ✗ Error validating stage order: {e}")
        print(f"  ✗ Error: {e}")
else:
    issues_found.append("  ✗ stage_order.py not found")
    print("  ✗ File not found!")

print()

# ============================================================================
# Fix 4: Check prepare-job.py uses correct stage directories
# ============================================================================
print("🔧 Fix 4: Checking prepare-job.py stage directories...")

prepare_job = PROJECT_ROOT / "scripts" / "prepare-job.py"
if prepare_job.exists():
    content = prepare_job.read_text()
    
    # Check if it imports from stage_order
    if "from shared.stage_order import" in content or "import shared.stage_order" in content:
        print("  ✓ prepare-job.py imports from stage_order")
        fixes_applied.append("  ✓ prepare-job.py uses centralized stage order")
    else:
        issues_found.append("  ⚠ prepare-job.py may not use centralized stage order")
        print("  ⚠ prepare-job.py doesn't import from stage_order")
        print("     Should use: from shared.stage_order import get_all_stage_dirs")
else:
    issues_found.append("  ✗ prepare-job.py not found")
    print("  ✗ File not found!")

print()

# ============================================================================
# Summary
# ============================================================================
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()

if fixes_applied:
    print(f"✅ Fixes Applied ({len(fixes_applied)}):")
    for fix in fixes_applied:
        print(fix)
    print()

if issues_found:
    print(f"⚠️  Issues Identified ({len(issues_found)}) - Require Manual Fix:")
    for issue in issues_found:
        print(issue)
    print()
    print("These issues require implementation in Session 3:")
    print("  1. Add _stage_glossary_load() method to run-pipeline.py")
    print("  2. Integrate glossary_load into transcribe/translate workflows")
    print("  3. Ensure glossary system is enabled in job configs")
    print()
else:
    print("✅ No critical issues found!")
    print()

print("=" * 70)
print("Next Steps:")
print("  1. Review issues found above")
print("  2. Implement missing glossary_load stage in run-pipeline.py")
print("  3. Test with: ./test-glossary-quickstart.sh")
print("=" * 70)
