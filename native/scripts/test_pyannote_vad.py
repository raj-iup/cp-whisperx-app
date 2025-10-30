#!/usr/bin/env python3
"""
Test script for Pyannote VAD MPS implementation.
Validates that Pyannote VAD works correctly with the pipeline.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'native/utils')


def test_pyannote_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import torch
        import torchaudio
        from device_manager import get_device
        from native_logger import NativePipelineLogger
        from pyannote_vad_wrapper import PyannoteVAD, load_secrets
        from pyannote.audio import Pipeline
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_secrets_loading():
    """Test secrets.json loading for HF token."""
    print("\nTesting secrets loading...")
    try:
        from pyannote_vad_wrapper import load_secrets
        
        secrets = load_secrets()
        
        hf_token = secrets.get('hf_token') or secrets.get('pyannote_token')
        
        if not hf_token:
            print("✗ HuggingFace token not found in secrets.json")
            return False
        
        print("✓ HuggingFace token loaded successfully")
        print(f"  Token prefix: {hf_token[:10]}...")
        return True
        
    except Exception as e:
        print(f"✗ Secrets loading failed: {e}")
        return False


def test_device_detection():
    """Test device detection."""
    print("\nTesting device detection...")
    try:
        import torch
        from device_manager import get_device
        
        print(f"  MPS available: {torch.backends.mps.is_available()}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        
        device = get_device(prefer_mps=False, stage_name='pyannote-vad')
        print(f"  Selected device: {device}")
        
        print("✓ Device detection working")
        return True
    except Exception as e:
        print(f"✗ Device detection failed: {e}")
        return False


def test_pyannote_model_load():
    """Test Pyannote VAD model loading."""
    print("\nTesting Pyannote VAD model loading...")
    try:
        from device_manager import get_device
        from pyannote_vad_wrapper import PyannoteVAD, load_secrets
        
        secrets = load_secrets()
        hf_token = secrets.get('hf_token') or secrets.get('pyannote_token')
        
        device = get_device(prefer_mps=False, stage_name='pyannote-vad')
        print(f"  Loading model on device: {device}")
        
        vad = PyannoteVAD(hf_token=hf_token, device=device)
        success = vad.load_model()
        
        if success and vad.pipeline is not None:
            print("✓ Pyannote VAD pipeline loaded successfully")
            print(f"  Model loaded: voice-activity-detection")
            return True
        else:
            print("✗ Model loading failed")
            return False
            
    except Exception as e:
        print(f"✗ Model load test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coarse_segments_exist():
    """Test that Silero VAD output exists."""
    print("\nTesting Silero VAD output availability...")
    try:
        coarse_file = Path("out/Jaane_Tu_Ya_Jaane_Na_2008/vad/silero_segments.json")
        
        if not coarse_file.exists():
            print(f"⚠ Silero segments not found: {coarse_file}")
            print("  Run Silero VAD stage first")
            return False
        
        with open(coarse_file, 'r') as f:
            data = json.load(f)
        
        segments = data.get('segments', [])
        print(f"✓ Silero segments file found")
        print(f"  Segments: {len(segments)}")
        print(f"  Duration: {data['statistics']['total_duration']:.2f}s")
        return True
        
    except Exception as e:
        print(f"✗ Coarse segments check failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Pyannote VAD Implementation Test Suite")
    print("="*60)
    
    tests = [
        ("Imports", test_pyannote_imports),
        ("Secrets Loading", test_secrets_loading),
        ("Device Detection", test_device_detection),
        ("Pyannote Model Load", test_pyannote_model_load),
        ("Silero Segments Available", test_coarse_segments_exist),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Pyannote VAD is ready for the pipeline.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
