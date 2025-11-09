#!/usr/bin/env python3
"""
Verify PyTorch installation and compatibility.
"""
import sys
import warnings

def verify_pytorch():
    """Verify PyTorch installation and show version information."""
    try:
        import torch
        import torchaudio
        
        print(f"✓ PyTorch version: {torch.__version__}")
        print(f"✓ TorchAudio version: {torchaudio.__version__}")
        
        # Check CUDA availability
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("✓ MPS (Metal) available: Apple Silicon GPU")
        else:
            print("✓ Running on CPU")
        
        # Check for known compatibility issues
        torch_version = tuple(map(int, torch.__version__.split('.')[:2]))
        torchaudio_version = tuple(map(int, torchaudio.__version__.split('.')[:2]))
        
        if torch_version != torchaudio_version:
            print(f"⚠ Warning: torch {torch.__version__} and torchaudio {torchaudio.__version__} versions don't match")
            print("  This may cause compatibility issues with pyannote.audio")
        
        return 0
        
    except ImportError as e:
        print(f"✗ PyTorch import failed: {e}")
        return 1
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return 1

if __name__ == "__main__":
    # Suppress warnings during verification
    warnings.filterwarnings('ignore')
    sys.exit(verify_pytorch())
