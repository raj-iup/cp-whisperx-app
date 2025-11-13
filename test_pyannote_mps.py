#!/usr/bin/env python3
"""
Quick test to verify PyAnnote VAD works with MPS device
"""
import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_pyannote_mps():
    """Test PyAnnote VAD on MPS device"""
    import torch
    from pyannote.audio import Pipeline
    
    print("="*70)
    print("Testing PyAnnote VAD with MPS")
    print("="*70)
    print()
    
    # Check MPS availability
    print(f"PyTorch version: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print()
    
    # Get HF token from environment
    config_path = os.environ.get('CONFIG_PATH')
    if not config_path:
        print("⚠️  CONFIG_PATH not set, trying default...")
        config_path = "config/.env.pipeline"
    
    hf_token = None
    if Path(config_path).exists():
        from shared.config import load_config
        config = load_config(config_path)
        hf_token = getattr(config, 'hf_token', None)
    
    if not hf_token:
        hf_token = os.environ.get('HF_TOKEN')
    
    if not hf_token:
        print("❌ No HF_TOKEN found!")
        print("Please set HF_TOKEN environment variable or in config")
        return False
    
    print(f"✓ HF Token found: {hf_token[:20]}...")
    print()
    
    # Load pipeline
    print("Loading PyAnnote VAD pipeline...")
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/voice-activity-detection",
            use_auth_token=hf_token
        )
        if pipeline is None:
            print("❌ Pipeline loaded but returned None")
            print("This usually means the model is gated and you need to accept the terms.")
            return False
        print("✓ Pipeline loaded")
    except Exception as e:
        print(f"❌ Failed to load pipeline: {e}")
        print("\nPlease:")
        print("1. Visit: https://huggingface.co/pyannote/voice-activity-detection")
        print("2. Click 'Agree and access repository'")
        print("3. Make sure your HF token has access")
        return False
    
    # Test moving to MPS
    print()
    print("Testing device placement...")
    devices = ['cpu', 'mps']
    
    for device in devices:
        if device == 'mps' and not torch.backends.mps.is_available():
            print(f"⊘ Skipping {device} (not available)")
            continue
        
        try:
            print(f"  Moving pipeline to {device}...")
            pipeline.to(device)
            print(f"  ✓ Successfully moved to {device}")
        except Exception as e:
            print(f"  ❌ Failed to move to {device}: {e}")
            if device == 'mps':
                return False
    
    print()
    print("="*70)
    print("✅ PyAnnote VAD MPS test PASSED")
    print("="*70)
    return True

if __name__ == "__main__":
    success = test_pyannote_mps()
    sys.exit(0 if success else 1)
