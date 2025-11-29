#!/usr/bin/env python3
"""
test_indictrans2.py - Test script for IndicTrans2 model setup

Verifies:
1. PyTorch MPS/GPU availability
2. IndicTrans2 model loading and inference
3. Hindi to English translation capability
"""

import torch
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_pytorch_device():
    """Test PyTorch and device availability"""
    print("=" * 60)
    print("PYTORCH DEVICE CHECK")
    print("=" * 60)
    print(f"PyTorch version: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print(f"MPS built: {torch.backends.mps.is_built()}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    # Determine best device
    if torch.backends.mps.is_available():
        device = "mps"
        print(f"\n✓ Using device: {device} (Apple Silicon GPU)")
    elif torch.cuda.is_available():
        device = "cuda"
        print(f"\n✓ Using device: {device} (NVIDIA GPU)")
    else:
        device = "cpu"
        print(f"\n✓ Using device: {device}")
    
    return device


def test_indictrans2_import():
    """Test IndicTrans2 module import"""
    print("\n" + "=" * 60)
    print("INDICTRANS2 MODULE CHECK")
    print("=" * 60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        print("✓ transformers library available")
    except ImportError as e:
        print(f"✗ transformers not available: {e}")
        print("\nInstall with:")
        print("  pip install 'transformers>=4.44'")
        return False
    
    try:
        import sentencepiece
        print("✓ sentencepiece available")
    except ImportError:
        print("✗ sentencepiece not available")
        print("\nInstall with:")
        print("  pip install sentencepiece")
        return False
    
    try:
        import sacremoses
        print("✓ sacremoses available")
    except ImportError:
        print("✗ sacremoses not available")
        print("\nInstall with:")
        print("  pip install sacremoses")
        return False
    
    try:
        import srt
        print("✓ srt library available")
    except ImportError:
        print("✗ srt library not available")
        print("\nInstall with:")
        print("  pip install srt")
        return False
    
    return True


def test_indictrans2_model(device: str = "mps"):
    """Test IndicTrans2 model loading and translation"""
    print("\n" + "=" * 60)
    print("INDICTRANS2 MODEL TEST")
    print("=" * 60)
    
    try:
        from indictrans2_translator import IndicTrans2Translator, TranslationConfig
        print("✓ IndicTrans2 translator module imported")
    except ImportError as e:
        print(f"✗ Failed to import indictrans2_translator: {e}")
        return False
    
    try:
        # Create config
        config = TranslationConfig(device=device)
        print(f"\nConfiguration:")
        print(f"  Model: {config.model_name}")
        print(f"  Device: {device}")
        print(f"  Source: {config.src_lang}")
        print(f"  Target: {config.tgt_lang}")
        print(f"  Beams: {config.num_beams}")
        
        # Create translator
        print("\nLoading model...")
        translator = IndicTrans2Translator(config=config)
        translator.load_model()
        
        # Test translations
        test_cases = [
            "मेरा नाम राज है और मैं ह्यूस्टन में रहता हूँ।",
            "आज मौसम बहुत अच्छा है।",
            "क्या आप हिंदी बोलते हैं?",
            "यह फिल्म बहुत अच्छी है।"
        ]
        
        print("\n" + "-" * 60)
        print("TRANSLATION TESTS")
        print("-" * 60)
        
        for i, hindi_text in enumerate(test_cases, 1):
            english_text = translator.translate_text(hindi_text, skip_english=False)
            print(f"\n{i}. Hindi: {hindi_text}")
            print(f"   English: {english_text}")
        
        # Test Hinglish (mixed Hindi-English)
        print("\n" + "-" * 60)
        print("HINGLISH TEST (skip_english=True)")
        print("-" * 60)
        
        hinglish_cases = [
            "Hello, मेरा नाम राज है",  # Mixed
            "This is already English",  # Pure English
            "यह हिंदी में है"  # Pure Hindi
        ]
        
        for i, text in enumerate(hinglish_cases, 1):
            result = translator.translate_text(text, skip_english=True)
            skipped = result == text
            print(f"\n{i}. Input: {text}")
            print(f"   Output: {result}")
            print(f"   {'(skipped - mostly English)' if skipped else '(translated)'}")
        
        # Cleanup
        translator.cleanup()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "IndicTrans2 Setup Verification" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Test 1: PyTorch device
    device = test_pytorch_device()
    
    # Test 2: Import check
    if not test_indictrans2_import():
        print("\n✗ Import test failed - install missing dependencies")
        return 1
    
    # Test 3: Model test
    if not test_indictrans2_model(device):
        print("\n✗ Model test failed")
        return 1
    
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    print("✓ PyTorch configured correctly")
    print("✓ All dependencies installed")
    print("✓ IndicTrans2 model working")
    print("\nYou can now use IndicTrans2 for Hindi→English translation!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
