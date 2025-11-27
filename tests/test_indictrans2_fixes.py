#!/usr/bin/env python3
"""
Test script to validate IndicTrans2 translator fixes.
Tests the problematic segments from the log file.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from indictrans2_translator import (
    IndicTrans2Translator,
    TranslationConfig,
    get_indictrans2_lang_code,
)

# Test cases from the log file that were failing
TEST_CASES = [
    "बैंड? क्यों?",
    "वो कुछ बॉम थर्क का लफड़ा है यार",
    "नहीं",
    "हुँ",
    "ओके",
    "चाहिक है",
    "कहानी शुरू होती है",
    "एक सपने से",
    "मैं कुछ कहना चाहता हूँ",
    "राधा बिल्ली थी",
    "आतती मार कभी कभी सार",
    "तु खुश है तो लगे के जहां में चाई जाए",
    # Empty and short cases
    "",
    ".",
    "...",
]


def main():
    """Test the translator with problematic cases"""
    print("=" * 70)
    print("IndicTrans2 Translator Fix Validation")
    print("=" * 70)
    print()
    
    # Get language codes
    src_lang = "hi"
    tgt_lang = "gu"
    src_lang_code = get_indictrans2_lang_code(src_lang)
    tgt_lang_code = get_indictrans2_lang_code(tgt_lang)
    
    print(f"Language pair: {src_lang} ({src_lang_code}) → {tgt_lang} ({tgt_lang_code})")
    print(f"Model: ai4bharat/indictrans2-indic-indic-1B")
    print()
    
    # Create configuration
    config = TranslationConfig(
        model_name="ai4bharat/indictrans2-indic-indic-1B",
        src_lang=src_lang_code,
        tgt_lang=tgt_lang_code,
        device="auto",
        batch_size=1,  # Process one at a time for testing
    )
    
    # Create translator
    print("Loading model...")
    translator = IndicTrans2Translator(
        config=config,
        source_lang=src_lang,
        target_lang=tgt_lang
    )
    
    try:
        translator.load_model()
        print("✓ Model loaded successfully")
        print()
        
        # Test each case
        print("-" * 70)
        print("Testing translation for problematic segments:")
        print("-" * 70)
        
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        for i, text in enumerate(TEST_CASES, 1):
            print(f"\n{i}. Input: '{text}'")
            
            # Check if text should be skipped
            if not text or len(text) <= 2:
                print(f"   → Skipped (empty or too short)")
                skipped_count += 1
                continue
            
            try:
                translation = translator.translate_text(text, skip_english=False)
                
                if translation == text:
                    print(f"   → Unchanged (fallback): '{translation}'")
                    failure_count += 1
                else:
                    print(f"   → Success: '{translation}'")
                    success_count += 1
                    
            except Exception as e:
                print(f"   → Error: {e}")
                failure_count += 1
        
        # Summary
        print()
        print("=" * 70)
        print("Test Summary:")
        print(f"  Total cases: {len(TEST_CASES)}")
        print(f"  Successful: {success_count}")
        print(f"  Failed/Fallback: {failure_count}")
        print(f"  Skipped: {skipped_count}")
        
        if failure_count == 0:
            print()
            print("✓ All tests passed! The fixes are working correctly.")
            return 0
        else:
            print()
            print(f"⚠ {failure_count} translations failed or fell back to original text.")
            print("  This may indicate preprocessing issues with the IndicTransToolkit.")
            return 1
            
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        translator.cleanup()
        print()
        print("Cleanup complete.")


if __name__ == "__main__":
    sys.exit(main())
