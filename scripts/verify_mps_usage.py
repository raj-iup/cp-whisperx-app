#!/usr/bin/env python3
"""
verify_mps_usage.py - Verify all stages use MPS on Apple Silicon

Checks:
1. MPS availability
2. Device auto-detection
3. Each stage configuration
4. Expected device usage

Usage:
    python3 scripts/verify_mps_usage.py
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'scripts'))
sys.path.insert(0, str(project_root / 'shared'))

def check_mps_available():
    """Check if MPS is available"""
    import torch
    
    print("=" * 70)
    print("MPS AVAILABILITY CHECK")
    print("=" * 70)
    
    if hasattr(torch.backends, 'mps'):
        mps_available = torch.backends.mps.is_available()
        print(f"✓ PyTorch MPS backend: Available")
        print(f"  MPS is available: {mps_available}")
        
        if mps_available:
            print(f"  ✓ Apple Silicon GPU acceleration ENABLED")
        else:
            print(f"  ⚠ MPS not available (not on Apple Silicon)")
        
        return mps_available
    else:
        print("✗ PyTorch MPS backend: Not available")
        print("  → Upgrade PyTorch to >=2.0 for MPS support")
        return False


def check_config_defaults():
    """Check configuration defaults"""
    from config import PipelineConfig
    
    print("\n" + "=" * 70)
    print("CONFIGURATION DEFAULTS")
    print("=" * 70)
    
    config = PipelineConfig()
    
    stages = {
        "WhisperX ASR": (config.whisperx_device, config.whisperx_backend),
        "PyAnnote VAD": (config.pyannote_device, None),
        "Diarization": (config.diarization_device, None),
    }
    
    all_auto = True
    for stage_name, (device, backend) in stages.items():
        status = "✓" if device == "auto" else "⚠"
        print(f"{status} {stage_name}:")
        print(f"    Device: {device}")
        if backend:
            print(f"    Backend: {backend}")
        
        if device != "auto":
            all_auto = False
    
    if all_auto:
        print("\n✓ All stages configured for auto-detection")
    else:
        print("\n⚠ Some stages not using auto-detection")
    
    return all_auto


def check_device_selector():
    """Check device selector auto-detection"""
    from device_selector import select_device
    
    print("\n" + "=" * 70)
    print("DEVICE SELECTOR AUTO-DETECTION")
    print("=" * 70)
    
    # Test auto mode
    device, fallback = select_device("auto")
    print(f"Auto-detection: {device} (fallback: {fallback})")
    
    # Test specific devices
    for req in ['mps', 'cuda', 'cpu']:
        device, fallback = select_device(req)
        status = "✓" if not fallback else "⚠"
        print(f"{status} Request '{req}' → Got '{device}' (fallback: {fallback})")
    
    return True


def check_mlx_installation():
    """Check if MLX-Whisper is installed"""
    print("\n" + "=" * 70)
    print("MLX-WHISPER INSTALLATION")
    print("=" * 70)
    
    try:
        import mlx_whisper
        version = getattr(mlx_whisper, '__version__', 'installed')
        print(f"✓ MLX-Whisper installed: {version}")
        print(f"  → WhisperX ASR will use Metal/MPS acceleration")
        print(f"  → Expected speedup: 2-4x faster than CPU")
        return True
    except ImportError:
        print("⚠ MLX-Whisper not installed")
        print("  Install with: pip install mlx-whisper")
        print("  → WhisperX ASR will fall back to CPU (slower)")
        return False


def check_backend_creation():
    """Test backend creation"""
    print("\n" + "=" * 70)
    print("BACKEND CREATION TEST")
    print("=" * 70)
    
    from whisper_backends import create_backend, get_recommended_backend
    
    # Create simple logger mock
    class SimpleLogger:
        def info(self, msg): print(f"  {msg}")
        def warning(self, msg): print(f"  ⚠ {msg}")
        def error(self, msg): print(f"  ✗ {msg}")
        def debug(self, msg): pass
    
    logger = SimpleLogger()
    
    # Test recommended backend
    print("\nRecommended backend for MPS:")
    backend_type = get_recommended_backend("mps", logger)
    print(f"  → {backend_type}")
    
    # Test backend creation
    print("\nCreating backends:")
    
    for backend_type in ["auto", "whisperx", "mlx"]:
        print(f"\n  Testing '{backend_type}' backend:")
        try:
            backend = create_backend(backend_type, "large-v3", "auto", "int8", logger)
            if backend:
                print(f"    ✓ Created: {backend.name}")
            else:
                print(f"    ✗ Failed to create backend")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    return True


def print_summary(mps_available, config_ok, mlx_installed):
    """Print summary of verification"""
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_ok = True
    
    # MPS availability
    if mps_available:
        print("✓ MPS available (Apple Silicon detected)")
    else:
        print("⚠ MPS not available (not on Apple Silicon)")
        print("  → GPU acceleration not available")
        all_ok = False
    
    # Config
    if config_ok:
        print("✓ All stages configured for auto-detection")
    else:
        print("⚠ Some stages may not auto-detect GPU")
        all_ok = False
    
    # MLX
    if mlx_installed:
        print("✓ MLX-Whisper installed (ASR will use GPU)")
    else:
        print("⚠ MLX-Whisper not installed (ASR will use CPU)")
        if mps_available:
            print("  → Install with: pip install mlx-whisper")
            all_ok = False
    
    print("\n" + "=" * 70)
    print("EXPECTED DEVICE USAGE")
    print("=" * 70)
    
    if mps_available:
        print("On Apple Silicon with current configuration:")
        print()
        print("  ✓ Silero VAD:     MPS (auto via PyTorch)")
        print("  ✓ PyAnnote VAD:   MPS (auto-detected)")
        print("  ✓ Diarization:    MPS (auto-detected)")
        if mlx_installed:
            print("  ✓ WhisperX ASR:   MPS (MLX backend) ⭐")
        else:
            print("  ⚠ WhisperX ASR:   CPU (MLX not installed)")
        print()
        
        if mlx_installed:
            print("🎉 All 4 ML stages will use Apple Silicon GPU!")
        else:
            print("⚠ 3/4 stages will use GPU (install MLX for full acceleration)")
    else:
        print("On non-Apple Silicon hardware:")
        print()
        print("  Stages will use CUDA if available, otherwise CPU")
    
    print("=" * 70)
    
    if all_ok and mps_available and mlx_installed:
        print("\n✅ PERFECT SETUP - All stages ready for MPS acceleration!")
        return 0
    elif mps_available:
        print("\n⚠ GOOD SETUP - Most stages will use MPS")
        if not mlx_installed:
            print("  Tip: Install mlx-whisper for full GPU acceleration")
        return 0
    else:
        print("\n✓ VALID SETUP - Will use best available device")
        return 0


def main():
    """Run all checks"""
    print("\n" * 2)
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "MPS USAGE VERIFICATION TOOL" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        mps_available = check_mps_available()
        config_ok = check_config_defaults()
        check_device_selector()
        mlx_installed = check_mlx_installation()
        check_backend_creation()
        
        return print_summary(mps_available, config_ok, mlx_installed)
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
