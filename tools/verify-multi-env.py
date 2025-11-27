#!/usr/bin/env python3
"""
Multi-Environment Architecture Verification Script
Verifies that all components are properly configured for multi-environment usage
"""

import json
import sys
from pathlib import Path

def main():
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "MULTI-ENVIRONMENT VERIFICATION" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    project_root = Path.cwd()
    success = True
    
    # Test 1: Check environments exist
    print("Test 1: Checking Virtual Environments")
    print("=" * 80)
    
    envs = {
        "common": ".venv-common",
        "whisperx": ".venv-whisperx",
        "mlx": ".venv-mlx",
        "indictrans2": ".venv-indictrans2"
    }
    
    for name, path in envs.items():
        env_path = project_root / path
        python_exe = env_path / "bin" / "python"
        
        if env_path.exists() and python_exe.exists():
            print(f"  ✅ {path:20} EXISTS → {python_exe}")
        else:
            print(f"  ❌ {path:20} MISSING")
            success = False
    
    print()
    
    # Test 2: Check EnvironmentManager
    print("Test 2: Environment Manager")
    print("=" * 80)
    
    try:
        # Add project root to Python path
        sys.path.insert(0, str(project_root))
        
        from shared.environment_manager import EnvironmentManager
        
        env_mgr = EnvironmentManager(project_root)
        print("  ✅ EnvironmentManager imported successfully")
        
        # Test stage mappings
        stages = ["demux", "asr", "alignment", "indictrans2_translation", "subtitle_generation"]
        print()
        print("  Stage-to-Environment Mappings:")
        for stage in stages:
            env_name = env_mgr.get_environment_for_stage(stage)
            print(f"    {stage:30} → .venv-{env_name}")
        
    except Exception as e:
        print(f"  ❌ EnvironmentManager error: {e}")
        env_mgr = None  # Set to None so later tests can check
        success = False
    
    print()
    
    # Test 3: Check hardware cache
    print("Test 3: Hardware Configuration")
    print("=" * 80)
    
    hardware_cache = project_root / "config" / "hardware_cache.json"
    if hardware_cache.exists():
        print(f"  ✅ Hardware cache exists: {hardware_cache}")
        
        with open(hardware_cache) as f:
            config = json.load(f)
        
        print(f"  Platform: {config.get('platform', 'unknown')}")
        print(f"  Processor: {config.get('processor', 'unknown')}")
        print(f"  Python: {config.get('python_version', 'unknown')}")
        
        if "stage_environments" in config:
            print(f"  Stage environments: {len(config['stage_environments'])} configured")
        else:
            print("  ⚠️  Stage environments not configured")
    else:
        print(f"  ❌ Hardware cache missing: {hardware_cache}")
        print("  Run: ./bootstrap.sh")
        success = False
    
    print()
    
    # Test 4: Check scripts
    print("Test 4: Script Configuration")
    print("=" * 80)
    
    scripts_to_check = [
        ("prepare-job.sh", "NOT_USED_ANYMORE"),
        ("run-pipeline.sh", "NOT_USED_ANYMORE"),
        ("scripts/run-pipeline.py", '["python",')
    ]
    
    for script, bad_pattern in scripts_to_check:
        script_path = project_root / script
        if script_path.exists():
            content = script_path.read_text()
            if bad_pattern in content:
                print(f"  ❌ {script}: Still contains '{bad_pattern}'")
                success = False
            else:
                print(f"  ✅ {script}: Properly updated")
        else:
            print(f"  ⚠️  {script}: Not found")
    
    print()
    
    # Test 5: Python executable resolution
    print("Test 5: Python Executable Resolution")
    print("=" * 80)
    
    if env_mgr:
        try:
            for env_name in ["common", "whisperx", "mlx", "indictrans2"]:
                if env_mgr.is_environment_installed(env_name):
                    python_exe = env_mgr.get_python_executable(env_name)
                    print(f"  ✅ {env_name:15} → {python_exe}")
                else:
                    print(f"  ❌ {env_name:15} → NOT INSTALLED")
                    if env_name not in ["mlx", "indictrans2"]:  # These are optional
                        success = False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            success = False
    else:
        print("  ⚠️  Skipped (EnvironmentManager not loaded)")
        success = False
    
    print()
    
    # Final summary
    print("=" * 80)
    if success:
        print("✅ ALL TESTS PASSED")
        print()
        print("Multi-environment architecture is properly configured!")
        print()
        print("Next steps:")
        print("  1. Test with real media:")
        print("     ./prepare-job.sh movie.mp4 --transcribe -s hi")
        print("     ./run-pipeline.sh -j <job-id>")
        print()
        print("  2. Verify MLX is used (Apple Silicon):")
        print("     grep 'Using MLX environment' out/.../job/logs/pipeline.log")
        print()
        print("  3. Check performance improvement:")
        print("     Compare transcription time vs CPU baseline")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Run ./bootstrap.sh to create environments")
        print("  - Check that code changes were applied correctly")
        return 1

if __name__ == "__main__":
    sys.exit(main())
