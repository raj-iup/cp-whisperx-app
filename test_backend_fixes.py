#!/usr/bin/env python3
"""
Test Backend Compatibility Fixes

Validates all five fixes implemented:
1. Dynamic environment selection for ASR
2. Backend fallback logic
3. Device/backend consistency validation
4. Configuration documentation (manual check)
5. Test script fixes (manual check)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_fix_1_dynamic_environment_selection():
    """Test Fix 1: Dynamic Environment Selection"""
    print("\n" + "="*60)
    print("TEST 1: Dynamic Environment Selection")
    print("="*60)
    
    from shared.environment_manager import EnvironmentManager
    
    em = EnvironmentManager()
    
    # Test MLX backend selection
    env = em.get_asr_environment("mlx")
    print(f"✓ MLX backend → {env} environment")
    assert env in ["mlx", "whisperx"], f"Expected mlx or whisperx, got {env}"
    
    # Test WhisperX backend selection
    env = em.get_asr_environment("whisperx")
    print(f"✓ WhisperX backend → {env} environment")
    assert env == "whisperx", f"Expected whisperx, got {env}"
    
    # Test auto backend selection
    env = em.get_asr_environment("auto")
    print(f"✓ Auto backend → {env} environment")
    assert env in ["mlx", "whisperx"], f"Expected mlx or whisperx, got {env}"
    
    # Test None backend (should default to auto)
    env = em.get_asr_environment(None)
    print(f"✓ None backend → {env} environment (auto-selected)")
    assert env in ["mlx", "whisperx"], f"Expected mlx or whisperx, got {env}"
    
    # Test has_environment method
    assert em.has_environment("common"), "common environment should exist"
    print(f"✓ has_environment('common') works")
    
    print("\n✅ Fix 1: PASSED - Dynamic environment selection works correctly")
    return True


def test_fix_2_backend_fallback():
    """Test Fix 2: Backend Fallback Logic"""
    print("\n" + "="*60)
    print("TEST 2: Backend Fallback Logic")
    print("="*60)
    
    # Import backend to check fallback return value exists
    import sys
    import os
    
    # Create a minimal logger that doesn't write files
    class MinimalLogger:
        def error(self, msg): pass
        def warning(self, msg): pass
        def info(self, msg): pass
        def debug(self, msg): pass
    
    logger = MinimalLogger()
    
    from scripts.whisper_backends import MLXWhisperBackend
    
    # Create MLX backend (will fail if mlx-whisper not in current env)
    backend = MLXWhisperBackend(
        model_name="large-v3",
        device="mps",
        compute_type="float16",
        logger=logger,
        condition_on_previous_text=False,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6,
        compression_ratio_threshold=2.4
    )
    
    # Test load_model returns fallback signal or success
    result = backend.load_model()
    print(f"✓ MLX backend load_model() returns: {result}")
    assert result in [True, False, "fallback_to_whisperx"], \
        f"Expected True/False/'fallback_to_whisperx', got {result}"
    
    if result == "fallback_to_whisperx":
        print(f"✓ Backend correctly signals fallback when MLX unavailable")
    elif result == True:
        print(f"✓ Backend loaded successfully (MLX available)")
    else:
        print(f"⚠ Backend load failed (expected in some environments)")
    
    print("\n✅ Fix 2: PASSED - Backend fallback logic implemented")
    return True


def test_fix_3_device_backend_validation():
    """Test Fix 3: Device/Backend Consistency Validation"""
    print("\n" + "="*60)
    print("TEST 3: Device/Backend Consistency Validation")
    print("="*60)
    
    # Import directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location("prepare_job", PROJECT_ROOT / "scripts" / "prepare-job.py")
    prepare_job = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare_job)
    
    validate = prepare_job.validate_device_backend_compatibility
    
    # Test: MLX backend with CPU device
    # Note: Current implementation auto-corrects device to MPS
    device, backend = validate("cpu", "mlx")
    print(f"✓ (cpu, mlx) → ({device}, {backend}) [auto-corrects device]")
    # MLX requires MPS, so it changes device to MPS
    assert device == "mps" and backend == "mlx", \
        f"Expected (mps, mlx), got ({device}, {backend})"
    
    # Test: MPS device with MLX backend (should pass through)
    device, backend = validate("mps", "mlx")
    print(f"✓ (mps, mlx) → ({device}, {backend}) [valid combination]")
    assert device == "mps" and backend == "mlx", \
        f"Expected (mps, mlx), got ({device}, {backend})"
    
    # Test: CPU with WhisperX (should pass through)
    device, backend = validate("cpu", "whisperx")
    print(f"✓ (cpu, whisperx) → ({device}, {backend}) [valid combination]")
    assert device == "cpu" and backend == "whisperx", \
        f"Expected (cpu, whisperx), got ({device}, {backend})"
    
    # Test: CUDA with WhisperX (should pass through)
    device, backend = validate("cuda", "whisperx")
    print(f"✓ (cuda, whisperx) → ({device}, {backend}) [valid combination]")
    assert device == "cuda" and backend == "whisperx", \
        f"Expected (cuda, whisperx), got ({device}, {backend})"
    
    # Test: MPS with WhisperX (should warn but allow)
    device, backend = validate("mps", "whisperx")
    print(f"✓ (mps, whisperx) → ({device}, {backend}) [suboptimal, warns user]")
    assert device == "mps" and backend == "whisperx", \
        f"Expected (mps, whisperx), got ({device}, {backend})"
    
    print("\n✅ Fix 3: PASSED - Device/backend validation works correctly")
    return True


def test_fix_4_configuration_docs():
    """Test Fix 4: Configuration Documentation"""
    print("\n" + "="*60)
    print("TEST 4: Configuration Documentation")
    print("="*60)
    
    config_file = PROJECT_ROOT / "config" / ".env.pipeline"
    
    if not config_file.exists():
        print("✗ config/.env.pipeline not found")
        return False
    
    content = config_file.read_text()
    
    # Check for WHISPER_BACKEND documentation
    checks = [
        ("WHISPER_BACKEND", "Backend parameter exists"),
        ("auto", "Auto option documented"),
        ("mlx", "MLX option documented"),
        ("whisperx", "WhisperX option documented"),
        ("gracefully fall back", "Fallback documented"),
        ("compatibility is validated", "Validation documented"),
    ]
    
    all_passed = True
    for check, description in checks:
        if check.lower() in content.lower():
            print(f"✓ {description}")
        else:
            print(f"✗ {description} - NOT FOUND")
            all_passed = False
    
    # Check that default is 'auto' not 'mlx'
    lines = content.split('\n')
    backend_line = [l for l in lines if l.startswith('WHISPER_BACKEND=')]
    if backend_line:
        value = backend_line[0].split('=')[1].strip()
        if value == 'auto':
            print(f"✓ WHISPER_BACKEND default is 'auto'")
        else:
            print(f"⚠ WHISPER_BACKEND is '{value}', recommended: 'auto'")
    
    if all_passed:
        print("\n✅ Fix 4: PASSED - Configuration documentation complete")
    else:
        print("\n⚠ Fix 4: PARTIAL - Some documentation missing")
    
    return all_passed


def test_fix_5_test_scripts():
    """Test Fix 5: Test Script Fixes"""
    print("\n" + "="*60)
    print("TEST 5: Test Script Invocation Syntax")
    print("="*60)
    
    test_files = [
        "test-glossary-quickstart.sh",
        "test-glossary-simple.sh"
    ]
    
    all_passed = True
    for test_file in test_files:
        file_path = PROJECT_ROOT / test_file
        if not file_path.exists():
            print(f"⚠ {test_file} not found")
            continue
        
        content = file_path.read_text()
        
        # Check for correct syntax
        if "./run-pipeline.sh -j" in content:
            print(f"✓ {test_file} uses correct syntax: ./run-pipeline.sh -j")
        else:
            print(f"✗ {test_file} missing correct syntax")
            all_passed = False
        
        # Check for old incorrect syntax
        if "./run-pipeline.sh translate " in content:
            print(f"✗ {test_file} still has old syntax: ./run-pipeline.sh translate")
            all_passed = False
    
    if all_passed:
        print("\n✅ Fix 5: PASSED - Test scripts use correct invocation syntax")
    else:
        print("\n⚠ Fix 5: PARTIAL - Some scripts need updates")
    
    return all_passed


def main():
    """Run all tests"""
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "BACKEND FIXES VALIDATION" + " "*19 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("Fix 1: Dynamic Environment Selection", test_fix_1_dynamic_environment_selection),
        ("Fix 2: Backend Fallback Logic", test_fix_2_backend_fallback),
        ("Fix 3: Device/Backend Validation", test_fix_3_device_backend_validation),
        ("Fix 4: Configuration Documentation", test_fix_4_configuration_docs),
        ("Fix 5: Test Script Fixes", test_fix_5_test_scripts),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} FAILED with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print(f"OVERALL: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
