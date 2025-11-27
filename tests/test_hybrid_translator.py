#!/usr/bin/env python3
"""
Test Hybrid Translation System

Tests the hybrid translator with sample dialogue and song segments
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.hybrid_translator import HybridTranslator
from shared.logger import PipelineLogger


# Test data
TEST_SEGMENTS = [
    # Dialogue segments
    {
        "start": 19.0,
        "end": 23.64,
        "text": "सॉरी, यह हमारे ग्रुप का बहुत स्पेशल गाना है",
        "is_lyric": False
    },
    {
        "start": 23.64,
        "end": 27.5,
        "text": "सच, इसलिए कप पिरीट से चर्च गेट तक गाते हुए आए थे",
        "is_lyric": False
    },
    # Song segments
    {
        "start": 0.0,
        "end": 8.0,
        "text": "तेरा मुझसे है पहले का नाता कोई",
        "is_lyric": True
    },
    {
        "start": 8.0,
        "end": 19.0,
        "text": "यूं ही नहीं दिल लुभाता कोई, जाने तू या जाने ना",
        "is_lyric": True
    },
]

# Film context for Jaane Tu Ya Jaane Na
FILM_CONTEXT = """Film: Jaane Tu Ya Jaane Na (2008)
Setting: Mumbai, college friends group
Tone: Casual, youth-oriented, romantic comedy
Main characters: Jai "Rats" and Aditi "Meow" - best friends who don't realize they're in love
Theme song: "Jaane Tu Ya Jaane Na" - romantic uncertainty, questioning feelings
"""


def test_hybrid_translator(use_llm: bool = False):
    """Test the hybrid translator"""
    
    print("=" * 70)
    print(f"HYBRID TRANSLATION TEST (LLM: {use_llm})")
    print("=" * 70)
    print()
    
    # Create logger
    logger = PipelineLogger("test_hybrid")
    
    # Initialize translator
    translator = HybridTranslator(
        source_lang="hi",
        target_lang="en",
        film_context=FILM_CONTEXT if use_llm else None,
        use_llm_for_songs=use_llm,
        llm_provider="anthropic",
        logger=logger
    )
    
    # Load models
    print("Loading translation models...")
    try:
        translator.load_indictrans2()
        print("✓ IndicTrans2 loaded")
    except Exception as e:
        print(f"✗ Failed to load IndicTrans2: {e}")
        return 1
    
    if use_llm:
        try:
            translator.load_llm_client()
            print("✓ LLM client loaded")
        except Exception as e:
            print(f"⚠ LLM client not available: {e}")
            print("  Will use IndicTrans2 for all translations")
    
    print()
    
    # Translate segments
    print("Translating test segments...")
    print()
    
    for i, segment in enumerate(TEST_SEGMENTS):
        text = segment['text']
        is_song = segment['is_lyric']
        
        print(f"Segment {i+1}:")
        print(f"  Type: {'SONG' if is_song else 'DIALOGUE'}")
        print(f"  Original: {text}")
        
        # Translate
        result = translator.translate_segment(
            text=text,
            is_song=is_song,
            context={'timestamp': f"{segment['start']:.1f}s"}
        )
        
        print(f"  Translation: {result.text}")
        print(f"  Method: {result.method}")
        print(f"  Confidence: {result.confidence:.2f}")
        print()
    
    # Show statistics
    stats = translator.get_statistics()
    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print(f"Total segments: {stats['total_segments']}")
    print(f"Dialogue segments: {stats['dialogue_segments']}")
    print(f"Song segments: {stats['song_segments']}")
    print(f"IndicTrans2 used: {stats['indictrans2_used']}")
    print(f"LLM used: {stats['llm_used']}")
    print(f"Errors: {stats['errors']}")
    print()
    
    return 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Hybrid Translation System')
    parser.add_argument(
        '--use-llm',
        action='store_true',
        help='Use LLM for song translations (requires API key)'
    )
    
    args = parser.parse_args()
    
    # Test without LLM first
    print("\n" + "=" * 70)
    print("TEST 1: IndicTrans2 Only (Baseline)")
    print("=" * 70)
    test_hybrid_translator(use_llm=False)
    
    # Test with LLM if requested
    if args.use_llm:
        print("\n" + "=" * 70)
        print("TEST 2: Hybrid (IndicTrans2 + LLM)")
        print("=" * 70)
        test_hybrid_translator(use_llm=True)
    else:
        print("\n" + "=" * 70)
        print("To test with LLM:")
        print("  python test_hybrid_translator.py --use-llm")
        print()
        print("Required:")
        print("  1. Install LLM environment: ./install-llm.sh")
        print("  2. Add API key to config/secrets.json")
        print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
