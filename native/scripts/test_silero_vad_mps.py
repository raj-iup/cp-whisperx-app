#!/usr/bin/env python3
"""
Test script for Silero VAD MPS implementation.
Validates that Silero VAD works correctly with Apple Silicon MPS acceleration.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'native/utils')

def test_silero_vad_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import torch
        import torchaudio
        from device_manager import get_device
        from native_logger import NativePipelineLogger
        from silero_vad_wrapper import SileroVAD
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_device_detection():
    """Test MPS device detection."""
    print("\nTesting device detection...")
    try:
        import torch
        from device_manager import get_device
        
        print(f"  MPS available: {torch.backends.mps.is_available()}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        
        device = get_device(prefer_mps=True, stage_name='silero-vad')
        print(f"  Selected device: {device}")
        
        if device == 'mps':
            print("✓ MPS device detected and selected")
        elif device == 'cpu':
            print("⚠ Fallback to CPU (MPS may not be available)")
        
        return True
    except Exception as e:
        print(f"✗ Device detection failed: {e}")
        return False

def test_silero_model_load():
    """Test Silero VAD model loading."""
    print("\nTesting Silero VAD model loading...")
    try:
        from device_manager import get_device
        from silero_vad_wrapper import SileroVAD
        
        device = get_device(prefer_mps=True, stage_name='silero-vad')
        print(f"  Loading model on device: {device}")
        
        vad = SileroVAD(device=device)
        success = vad.load_model()
        
        if success and vad.model is not None:
            print("✓ Silero VAD model loaded successfully")
            print(f"  Model device: {next(vad.model.parameters()).device}")
            return True
        else:
            print("✗ Model loading failed")
            return False
            
    except Exception as e:
        print(f"✗ Model load test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_secrets_loading():
    """Test secrets.json loading (required for other stages)."""
    print("\nTesting secrets.json access...")
    try:
        secrets_path = Path('config/secrets.json')
        
        if not secrets_path.exists():
            print(f"⚠ Warning: {secrets_path} not found")
            print("  This is needed for TMDB and Pyannote stages")
            return False
        
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
        
        expected_keys = ['hf_token', 'tmdb_api_key', 'pyannote_token']
        missing_keys = [key for key in expected_keys if key not in secrets]
        
        if missing_keys:
            print(f"⚠ Missing keys in secrets.json: {missing_keys}")
            return False
        
        print("✓ secrets.json loaded successfully")
        print(f"  Available keys: {list(secrets.keys())}")
        return True
        
    except Exception as e:
        print(f"✗ Secrets loading failed: {e}")
        return False

def test_manifest_creation():
    """Test manifest system."""
    print("\nTesting manifest system...")
    try:
        from manifest import StageManifest
        from pathlib import Path
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            movie_dir = Path(tmpdir) / "test_movie"
            movie_dir.mkdir()
            
            with StageManifest('silero-vad', movie_dir) as manifest:
                manifest.add_metadata('test_key', 'test_value')
                manifest.add_metadata('device', 'mps')
            
            manifest_file = movie_dir / 'manifest.json'
            if manifest_file.exists():
                with open(manifest_file) as f:
                    data = json.load(f)
                print("✓ Manifest created successfully")
                print(f"  Stage status: {data['stages']['silero-vad']['status']}")
                return True
            else:
                print("✗ Manifest file not created")
                return False
                
    except Exception as e:
        print(f"✗ Manifest test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("Silero VAD MPS Implementation Test Suite")
    print("="*60)
    
    tests = [
        ("Imports", test_silero_vad_imports),
        ("Device Detection", test_device_detection),
        ("Silero Model Load", test_silero_model_load),
        ("Secrets Loading", test_secrets_loading),
        ("Manifest System", test_manifest_creation),
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
        print("\n🎉 All tests passed! Silero VAD is ready for MPS pipeline.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
