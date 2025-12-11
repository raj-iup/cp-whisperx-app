#!/usr/bin/env python3
"""
Phase 3 E2E Testing: Dry Run Validator

Validates that the pipeline can execute without running actual ML models.
Tests stage-to-stage communication, manifest tracking, and error handling.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_stage_interfaces() -> bool:
    """Test that all stages have proper interfaces."""
    print("=" * 60)
    print("Testing Stage Interfaces")
    print("=" * 60)
    
    stages = [
        "01_demux", "02_tmdb_enrichment", "03_glossary_loader",
        "04_source_separation", "05_pyannote_vad", "06_whisperx_asr",
        "07_alignment", "08_translation", "09_subtitle_generation", "10_mux"
    ]
    
    all_passed = True
    for stage in stages:
        try:
            import importlib
            module = importlib.import_module(f"scripts.{stage}")
            
            # Check for run_stage function
            if not hasattr(module, "run_stage"):
                print(f"  ✗ {stage}: Missing run_stage()")
                all_passed = False
                continue
            
            # Check signature
            import inspect
            sig = inspect.signature(module.run_stage)
            params = list(sig.parameters.keys())
            
            if "job_dir" not in params:
                print(f"  ✗ {stage}: Missing job_dir parameter")
                all_passed = False
                continue
            
            if sig.return_annotation != int:
                print(f"  ⚠ {stage}: Return type not int (got {sig.return_annotation})")
            
            print(f"  ✓ {stage}: Interface OK")
            
        except Exception as e:
            print(f"  ✗ {stage}: {str(e)}")
            all_passed = False
    
    return all_passed

def test_job_structure(job_dir: Path) -> bool:
    """Test job directory structure."""
    print("\n" + "=" * 60)
    print("Testing Job Structure")
    print("=" * 60)
    print(f"Job directory: {job_dir}")
    
    all_passed = True
    
    # Check required files
    required_files = [
        "job.json",
        "manifest.json"
    ]
    
    for file in required_files:
        file_path = job_dir / file
        if file_path.exists():
            print(f"  ✓ {file} exists")
        else:
            print(f"  ✗ {file} missing")
            all_passed = False
    
    # Check job.json content
    job_json = job_dir / "job.json"
    if job_json.exists():
        try:
            with open(job_json) as f:
                job_data = json.load(f)
            
            required_keys = ["job_id", "workflow", "source_language", "input_media"]
            for key in required_keys:
                if key in job_data:
                    print(f"  ✓ job.json has '{key}': {job_data[key]}")
                else:
                    print(f"  ✗ job.json missing '{key}'")
                    all_passed = False
                    
        except Exception as e:
            print(f"  ✗ Failed to parse job.json: {e}")
            all_passed = False
    
    # Check stage directories
    expected_stages = [
        "01_demux", "02_tmdb", "03_glossary_load",
        "04_source_separation", "05_pyannote_vad", "06_asr",
        "07_alignment", "08_lyrics_detection", "09_export_transcript",
        "10_translation", "11_subtitle_generation", "12_mux"
    ]
    
    print("\nStage directories:")
    for stage in expected_stages:
        stage_dir = job_dir / stage
        if stage_dir.exists():
            print(f"  ✓ {stage}/")
        else:
            print(f"  ⚠ {stage}/ not created yet")
    
    return all_passed

def test_environment_config(job_dir: Path) -> bool:
    """Test environment configuration."""
    print("\n" + "=" * 60)
    print("Testing Environment Configuration")
    print("=" * 60)
    
    env_file = None
    for file in job_dir.glob(".job-*.env"):
        env_file = file
        break
    
    if not env_file:
        print("  ✗ No .env file found")
        return False
    
    print(f"  ✓ Found: {env_file.name}")
    
    # Parse env file
    config = {}
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        
        # Check critical config
        critical_keys = [
            "WORKFLOW",
            "SOURCE_LANGUAGE", 
            "DEVICE",
            "WHISPERX_MODEL"
        ]
        
        for key in critical_keys:
            if key in config:
                print(f"  ✓ {key}={config[key]}")
            else:
                print(f"  ⚠ {key} not set")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to parse env file: {e}")
        return False

def test_stage_execution_order() -> bool:
    """Test that we can determine stage execution order."""
    print("\n" + "=" * 60)
    print("Testing Stage Execution Order")
    print("=" * 60)
    
    try:
        from shared.stage_order import get_workflow_stages
        
        workflows = ["transcribe", "translate", "subtitle"]
        
        for workflow in workflows:
            try:
                stages = get_workflow_stages(workflow)
                print(f"\n  {workflow.upper()} workflow ({len(stages)} stages):")
                for i, stage in enumerate(stages, 1):
                    print(f"    {i}. {stage}")
            except Exception as e:
                print(f"  ✗ {workflow}: {e}")
                return False
        
        return True
        
    except ImportError:
        print("  ⚠ stage_order module not available")
        return False

def main():
    """Run all E2E dry-run tests."""
    print("\n" + "=" * 60)
    print("PHASE 3 E2E TESTING: DRY RUN VALIDATION")
    print("=" * 60)
    print("\nValidating pipeline readiness without running ML models\n")
    
    results = {}
    
    # Test 1: Stage interfaces
    results["interfaces"] = test_stage_interfaces()
    
    # Test 2: Job structure (use latest job)
    job_dirs = sorted(Path("out").rglob("job.json"))
    if job_dirs:
        job_dir = job_dirs[-1].parent
        results["job_structure"] = test_job_structure(job_dir)
        results["environment"] = test_environment_config(job_dir)
    else:
        print("\n⚠ No job directory found, skipping job structure tests")
        results["job_structure"] = False
        results["environment"] = False
    
    # Test 3: Stage execution order
    results["execution_order"] = test_stage_execution_order()
    
    # Summary
    print("\n" + "=" * 60)
    print("DRY RUN VALIDATION SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test:20s} {status}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All dry-run validations PASSED!")
        print("Pipeline is ready for full E2E testing with ML models.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("Fix issues before running full pipeline.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
