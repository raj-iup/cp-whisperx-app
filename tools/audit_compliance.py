#!/usr/bin/env python3
"""
Compliance Audit Tool - Verify 100% compliance across all stages

Checks all 10 pipeline stages against the 6 criteria:
1. StageIO pattern (with manifest tracking)
2. get_stage_logger() usage
3. load_config() usage
4. No hardcoded paths (uses STAGE_ORDER)
5. Comprehensive error handling with manifest.record_error()
6. Complete module docstring
"""
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Stage list
STAGES = [
    "demux",
    "tmdb",
    "glossary",
    "source_separation",
    "vad",
    "whisperx_integration",  # ASR
    "alignment",
    "lyrics_detection",
    "subtitle_generation",
    "mux"
]

# Criteria weights (all equal for 100%)
CRITERIA = {
    "stageio": "Uses StageIO pattern with manifest",
    "logger": "Uses get_stage_logger()",
    "config": "Uses load_config() or reads job.json",
    "paths": "No hardcoded paths (uses STAGE_ORDER)",
    "errors": "Comprehensive error handling with manifest.record_error()",
    "docs": "Complete module docstring"
}


def check_stage_file(stage_name: str, scripts_dir: Path) -> Dict[str, bool]:
    """Check a single stage file against all criteria."""
    # Map stage names to file names
    stage_files = {
        "demux": "demux.py",
        "tmdb": "tmdb_enrichment_stage.py",  # Updated
        "glossary": "glossary_builder.py",  # Updated
        "source_separation": "source_separation.py",
        "vad": "pyannote_vad.py",  # Updated
        "whisperx_integration": "whisperx_integration.py",
        "alignment": "mlx_alignment.py",  # Updated
        "lyrics_detection": "lyrics_detection.py",
        "subtitle_generation": "subtitle_gen.py",  # Updated
        "mux": "mux.py"
    }
    
    stage_file = scripts_dir / stage_files.get(stage_name, f"{stage_name}.py")
    
    if not stage_file.exists():
        return {key: False for key in CRITERIA.keys()}
    
    try:
        with open(stage_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Cannot read {stage_file}: {e}")
        return {key: False for key in CRITERIA.keys()}
    
    results = {}
    
    # Check 1: StageIO pattern with manifest
    stageio_pattern = r'StageIO\(["\'].*?["\'].*?enable_manifest\s*=\s*True'
    manifest_pattern = r'StageManifest\('
    results["stageio"] = bool(re.search(stageio_pattern, content) or 
                             re.search(manifest_pattern, content))
    
    # Check 2: get_stage_logger()
    logger_pattern = r'get_stage_logger\('
    results["logger"] = bool(re.search(logger_pattern, content))
    
    # Check 3: load_config() or job.json
    config_pattern = r'load_config\(|job\.json|job_config'
    results["config"] = bool(re.search(config_pattern, content))
    
    # Check 4: No hardcoded paths (uses STAGE_ORDER or relative paths)
    # Check for common hardcoded path patterns
    bad_paths = [
        r'["\']\/out\/',
        r'["\']\/tmp\/',
        r'["\']\/home\/',
        r'["\']\/Users\/',
        r'["\']C:\\',
        r'output_base\s*=\s*["\']/',
    ]
    has_hardcoded = any(re.search(pattern, content) for pattern in bad_paths)
    # Look for proper path usage
    good_paths = r'output_base|stage_dir|STAGE_ORDER|Path\(__file__\)'
    has_proper_paths = bool(re.search(good_paths, content))
    results["paths"] = has_proper_paths and not has_hardcoded
    
    # Check 5: Comprehensive error handling with manifest.record_error()
    # Must have try-except blocks
    has_try_except = bool(re.search(r'\btry\s*:', content))
    # Must have manifest.record_error() or add_error()
    has_error_tracking = bool(re.search(r'manifest\.record_error\(|add_error\(|stage_io\.add_error\(', content))
    # Must have finalize on error path
    has_finalize_error = bool(re.search(r'finalize\(.*?failed|finalize\(.*?error', content, re.IGNORECASE))
    # Count exception handlers
    exception_count = len(re.findall(r'except\s+\w+', content))
    # Comprehensive = all conditions met + multiple exception types
    results["errors"] = (has_try_except and 
                        has_error_tracking and 
                        has_finalize_error and 
                        exception_count >= 3)
    
    # Check 6: Complete module docstring
    # Check for docstring at beginning (after shebang/encoding)
    docstring_pattern = r'^(?:#![^\n]*\n)?(?:#.*?coding[^\n]*\n)?[\s\n]*["\'"]{3}[^"\']{20,}["\'"]{3}'
    results["docs"] = bool(re.search(docstring_pattern, content, re.MULTILINE | re.DOTALL))
    
    return results


def calculate_score(results: Dict[str, bool]) -> float:
    """Calculate compliance score (0-100%)."""
    if not results:
        return 0.0
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    return (passed / total) * 100.0


def print_stage_report(stage_name: str, results: Dict[str, bool], score: float):
    """Print detailed report for a single stage."""
    status = "✅" if score == 100.0 else ("⚠️" if score >= 80.0 else "❌")
    print(f"\n{status} {stage_name.upper()} - {score:.1f}%")
    print("-" * 50)
    
    for key, description in CRITERIA.items():
        passed = results.get(key, False)
        symbol = "✅" if passed else "❌"
        print(f"  {symbol} {description}")


def main():
    """Run compliance audit on all stages."""
    print("=" * 60)
    print("🔍 PIPELINE COMPLIANCE AUDIT")
    print("=" * 60)
    print(f"Checking {len(STAGES)} stages against {len(CRITERIA)} criteria")
    print()
    
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    if not scripts_dir.exists():
        print(f"ERROR: Scripts directory not found: {scripts_dir}")
        return 1
    
    # Check all stages
    all_results = {}
    all_scores = {}
    
    for stage in STAGES:
        results = check_stage_file(stage, scripts_dir)
        score = calculate_score(results)
        all_results[stage] = results
        all_scores[stage] = score
        print_stage_report(stage, results, score)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    perfect_stages = sum(1 for score in all_scores.values() if score == 100.0)
    good_stages = sum(1 for score in all_scores.values() if 80.0 <= score < 100.0)
    needs_work = sum(1 for score in all_scores.values() if score < 80.0)
    
    print(f"\n✅ Perfect (100%):     {perfect_stages}/{len(STAGES)} stages")
    print(f"⚠️  Good (80-99%):     {good_stages}/{len(STAGES)} stages")
    print(f"❌ Needs Work (<80%): {needs_work}/{len(STAGES)} stages")
    
    average_score = sum(all_scores.values()) / len(all_scores) if all_scores else 0.0
    print(f"\n📈 Average Score: {average_score:.1f}%")
    
    # Stages needing attention
    if perfect_stages < len(STAGES):
        print("\n🎯 STAGES NEEDING ATTENTION:")
        for stage, score in sorted(all_scores.items(), key=lambda x: x[1]):
            if score < 100.0:
                print(f"  • {stage}: {score:.1f}%")
                # Show which criteria failed
                failed = [desc for key, desc in CRITERIA.items() 
                         if not all_results[stage].get(key, False)]
                for fail in failed:
                    print(f"    - Missing: {fail}")
    
    # Overall status
    print("\n" + "=" * 60)
    if perfect_stages == len(STAGES):
        print("🎊 PERFECT! 100% COMPLIANCE ACHIEVED! 🎊")
        print("All stages meet all criteria!")
        return 0
    elif average_score >= 95.0:
        print(f"🎯 EXCELLENT! {average_score:.1f}% compliance")
        print("Almost there - minor fixes needed")
        return 0
    elif average_score >= 80.0:
        print(f"✅ GOOD! {average_score:.1f}% compliance")
        print("On track - some improvements needed")
        return 0
    else:
        print(f"⚠️  NEEDS WORK! {average_score:.1f}% compliance")
        print("Several stages need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
