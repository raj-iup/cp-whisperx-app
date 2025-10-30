#!/usr/bin/env python3
"""
Test HuggingFace model access for PyAnnote models
Run after accepting model terms on HuggingFace.co
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from scripts.config_loader import Config

def test_model_access(model_name: str, token: str) -> bool:
    """Test if we can access a HuggingFace model"""
    try:
        from huggingface_hub import hf_hub_download
        
        print(f"Testing access to: {model_name}")
        
        # Try to download config file (small, fast test)
        hf_hub_download(
            repo_id=model_name,
            filename="config.yaml",
            token=token,
            cache_dir="/tmp/hf_test"
        )
        
        print(f"✅ Access granted: {model_name}")
        return True
        
    except Exception as e:
        print(f"❌ Access denied: {model_name}")
        print(f"   Error: {str(e)[:100]}")
        return False


def main():
    print("="*70)
    print("HuggingFace Model Access Test")
    print("="*70)
    print()
    
    # Load config
    config = Config()
    hf_token = config.get_secret("hf_token")
    
    print(f"HF Token: {hf_token[:20]}...")
    print()
    
    # Test required models
    models = [
        "pyannote/segmentation",
        "pyannote/speaker-diarization-3.1",
        "pyannote/voice-activity-detection",
    ]
    
    results = {}
    for model in models:
        results[model] = test_model_access(model, hf_token)
        print()
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    
    for model, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {model}")
    
    print()
    
    if all(results.values()):
        print("🎉 ALL MODELS ACCESSIBLE!")
        print("You can now resume the pipeline.")
        return 0
    else:
        print("⚠️  SOME MODELS NOT ACCESSIBLE")
        print()
        print("Next steps:")
        print("1. Visit: https://huggingface.co/pyannote/segmentation")
        print("2. Click 'Agree and access repository'")
        print("3. Repeat for other models")
        print("4. Run this test again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
