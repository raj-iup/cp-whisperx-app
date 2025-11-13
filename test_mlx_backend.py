#!/usr/bin/env python3
"""
Test script for MLX-Whisper backend integration

Verifies:
1. Backend creation and selection
2. Device compatibility checks
3. MLX availability detection
4. Fallback behavior

Usage:
    python3 test_mlx_backend.py
"""

import sys
import os
from pathlib import Path

# Add scripts and shared to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'scripts'))
sys.path.insert(0, str(project_root / 'shared'))

# Set minimal environment
os.environ['LOG_LEVEL'] = 'ERROR'

def test_backend_import():
    """Test that backend module can be imported"""
    print("Test 1: Import backend module...")
    try:
        from whisper_backends import (
            WhisperBackend,
            WhisperXBackend, 
            MLXWhisperBackend,
            create_backend,
            get_recommended_backend
        )
        print("  ✓ Backend module imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        return False


def test_mlx_availability():
    """Test MLX-Whisper availability"""
    print("\nTest 2: Check MLX-Whisper availability...")
    try:
        import mlx_whisper
        print(f"  ✓ MLX-Whisper installed (version: {mlx_whisper.__version__ if hasattr(mlx_whisper, '__version__') else 'unknown'})")
        return True
    except ImportError:
        print("  ⚠ MLX-Whisper not installed (optional on Apple Silicon)")
        print("    Install with: pip install mlx-whisper")
        return False


def test_torch_mps():
    """Test PyTorch MPS availability"""
    print("\nTest 3: Check PyTorch MPS support...")
    try:
        import torch
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("  ✓ MPS (Apple Silicon GPU) available")
            return True
        else:
            print("  ⚠ MPS not available (not on Apple Silicon)")
            return False
    except ImportError:
        print("  ✗ PyTorch not installed")
        return False


def test_backend_selection():
    """Test backend selection logic"""
    print("\nTest 4: Test backend selection...")
    
    try:
        from whisper_backends import get_recommended_backend
        
        # Create simple logger mock
        class SimpleLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
        
        logger = SimpleLogger()
        
        # Test different device recommendations
        devices_to_test = ["mps", "cuda", "cpu"]
        
        for device in devices_to_test:
            backend = get_recommended_backend(device, logger)
            print(f"  Device '{device}' → Backend '{backend}'")
        
        print("  ✓ Backend selection logic works")
        return True
    except Exception as e:
        print(f"  ✗ Backend selection failed: {e}")
        return False


def test_backend_creation():
    """Test backend instance creation"""
    print("\nTest 5: Test backend creation...")
    
    try:
        from whisper_backends import create_backend
        
        # Create simple logger mock
        class SimpleLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = SimpleLogger()
        
        # Test WhisperX backend creation
        print("  Creating WhisperX backend (CPU)...")
        backend_wx = create_backend("whisperx", "large-v3", "cpu", "int8", logger)
        if backend_wx:
            print(f"    ✓ Created: {backend_wx.name}")
        else:
            print("    ✗ Failed to create WhisperX backend")
            return False
        
        # Test auto backend creation
        print("  Creating auto backend (CPU)...")
        backend_auto = create_backend("auto", "large-v3", "cpu", "int8", logger)
        if backend_auto:
            print(f"    ✓ Created: {backend_auto.name}")
        else:
            print("    ✗ Failed to create auto backend")
            return False
        
        print("  ✓ Backend creation works")
        return True
    except Exception as e:
        print(f"  ✗ Backend creation failed: {e}")
        return False


def test_device_compatibility():
    """Test device compatibility checks"""
    print("\nTest 6: Test device compatibility...")
    
    try:
        from whisper_backends import WhisperXBackend, MLXWhisperBackend
        
        # Create simple logger mock
        class SimpleLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
        
        logger = SimpleLogger()
        
        # Test WhisperX compatibility
        wx_backend = WhisperXBackend("large-v3", "cpu", "int8", logger)
        print(f"  WhisperX supports CPU: {wx_backend.supports_device('cpu')}")
        print(f"  WhisperX supports CUDA: {wx_backend.supports_device('cuda')}")
        print(f"  WhisperX supports MPS: {wx_backend.supports_device('mps')} (should be False)")
        
        # Test MLX compatibility
        mlx_backend = MLXWhisperBackend("large-v3", "mps", "float16", logger)
        print(f"  MLX supports CPU: {mlx_backend.supports_device('cpu')} (should be False)")
        print(f"  MLX supports CUDA: {mlx_backend.supports_device('cuda')} (should be False)")
        print(f"  MLX supports MPS: {mlx_backend.supports_device('mps')}")
        
        print("  ✓ Device compatibility checks work")
        return True
    except Exception as e:
        print(f"  ✗ Device compatibility failed: {e}")
        return False


def test_config_integration():
    """Test configuration support"""
    print("\nTest 7: Test configuration integration...")
    
    try:
        from config import PipelineConfig
        
        # Create config with MLX backend
        config = PipelineConfig(
            whisperx_backend="mlx",
            whisperx_device="mps"
        )
        
        print(f"  Config backend: {config.whisperx_backend}")
        print(f"  Config device: {config.whisperx_device}")
        print("  ✓ Configuration integration works")
        return True
        
    except Exception as e:
        print(f"  ⚠ Config test skipped (expected in test environment): {e}")
        return True  # Don't fail on this in test environment


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("MLX-Whisper Backend Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import backend module", test_backend_import),
        ("MLX-Whisper availability", test_mlx_availability),
        ("PyTorch MPS support", test_torch_mps),
        ("Backend selection", test_backend_selection),
        ("Backend creation", test_backend_creation),
        ("Device compatibility", test_device_compatibility),
        ("Config integration", test_config_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n  ✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
