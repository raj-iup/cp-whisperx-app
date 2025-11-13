#!/usr/bin/env python3
"""
Test ML-based Glossary Selection
Demonstrates the ML term selector functionality
"""

import sys
from pathlib import Path

# Add shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

import logging
from glossary_ml import MLTermSelector
from glossary_advanced import AdvancedGlossaryStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ml_selector():
    """Test ML selector directly"""
    print("=" * 70)
    print("Testing ML Term Selector")
    print("=" * 70)
    
    # Initialize ML selector
    selector = MLTermSelector(logger)
    
    print(f"\n✓ Initialized ML selector")
    print(f"  Model type: {selector.model_type}")
    print(f"  Available: {selector.is_available()}")
    
    # Test term: "yaar"
    term = "yaar"
    options = ["dude", "man", "friend", "buddy"]
    
    print(f"\n📝 Training ML selector with examples...")
    
    # Simulate training data - casual contexts prefer "dude"
    casual_contexts = [
        {"text": "Hey yaar, what's up?", "window": "", "term_context": "casual"},
        {"text": "Yo yaar, let's party!", "window": "", "term_context": "casual"},
        {"text": "Cool yaar, that's awesome!", "window": "", "term_context": "casual"},
    ]
    
    for ctx in casual_contexts:
        selector.record_selection(term, "dude", ctx)
        print(f"  ✓ Recorded: '{term}' → 'dude' (casual)")
    
    # Formal contexts prefer "friend"
    formal_contexts = [
        {"text": "Thank you yaar, I appreciate it.", "window": "", "term_context": "formal"},
        {"text": "Please yaar, help me with this.", "window": "", "term_context": "formal"},
    ]
    
    for ctx in formal_contexts:
        selector.record_selection(term, "friend", ctx)
        print(f"  ✓ Recorded: '{term}' → 'friend' (formal)")
    
    # Test predictions
    print(f"\n🔮 Testing predictions...")
    
    # Test 1: Casual context
    test_casual = {
        "text": "Hey yaar, this is cool!",
        "window": "",
        "term_context": "casual"
    }
    predicted, confidence = selector.predict(term, options, test_casual)
    print(f"\n  Test 1 - Casual context:")
    print(f"    Input: 'Hey yaar, this is cool!'")
    print(f"    Predicted: '{predicted}' (confidence: {confidence:.2%})")
    print(f"    Expected: 'dude' ✓" if predicted == "dude" else f"    Expected: 'dude' ✗")
    
    # Test 2: Formal context
    test_formal = {
        "text": "Thank you yaar, that's kind of you.",
        "window": "",
        "term_context": "formal"
    }
    predicted, confidence = selector.predict(term, options, test_formal)
    print(f"\n  Test 2 - Formal context:")
    print(f"    Input: 'Thank you yaar, that's kind of you.'")
    print(f"    Predicted: '{predicted}' (confidence: {confidence:.2%})")
    print(f"    Expected: 'friend' ✓" if predicted == "friend" else f"    Expected: 'friend' ✗")
    
    # Show statistics
    stats = selector.get_statistics()
    print(f"\n📊 ML Selector Statistics:")
    print(f"  Model type: {stats['model_type']}")
    print(f"  Training examples: {stats['total_training_examples']}")
    print(f"  Terms learned: {stats['terms_learned']}")
    print(f"  Avg examples/term: {stats['avg_examples_per_term']:.1f}")
    
    # Test save/load
    print(f"\n💾 Testing save/load...")
    test_file = Path(__file__).parent / "test_ml_model.json"
    selector.save_model(test_file)
    
    # Load into new selector
    new_selector = MLTermSelector(logger)
    new_selector.load_model(test_file)
    
    # Verify loaded model works
    predicted, confidence = new_selector.predict(term, options, test_casual)
    print(f"  ✓ Loaded model prediction: '{predicted}' (confidence: {confidence:.2%})")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print(f"  ✓ Cleaned up test file")


def test_integrated_strategy():
    """Test ML selector integrated with AdvancedGlossaryStrategy"""
    print("\n" + "=" * 70)
    print("Testing Integrated ML Strategy")
    print("=" * 70)
    
    # Initialize with ML strategy
    strategy = AdvancedGlossaryStrategy(strategy='ml', logger=logger)
    
    print(f"\n✓ Initialized advanced strategy")
    print(f"  Strategy: {strategy.strategy}")
    print(f"  ML selector available: {strategy.ml_selector is not None}")
    
    if strategy.ml_selector:
        print(f"  ML model type: {strategy.ml_selector.model_type}")
    
    # Test term selection
    term = "bhai"
    options = ["brother", "bro", "dude"]
    
    print(f"\n📝 Testing term selection through strategy...")
    
    # Train with some examples
    contexts = [
        {
            "text": "Hey bhai, come here!",
            "window": "",
            "speaker": "Young Guy",
            "term_context": "casual"
        },
        {
            "text": "My dear bhai, I need your help.",
            "window": "",
            "speaker": "Elder Brother",
            "term_context": "formal"
        },
    ]
    
    # Record some selections
    for i, ctx in enumerate(contexts):
        selected = strategy.select_best_option(term, options, ctx)
        print(f"  Selection {i+1}: '{term}' → '{selected}' ({ctx.get('term_context')})")
    
    # Show final statistics
    stats = strategy.get_statistics()
    print(f"\n📊 Strategy Statistics:")
    print(f"  Strategy: {stats['strategy']}")
    print(f"  Character profiles: {stats['character_profiles']}")
    print(f"  Regional variant: {stats['regional_variant']}")
    
    if 'ml_stats' in stats:
        print(f"  ML training examples: {stats['ml_stats']['total_training_examples']}")
        print(f"  ML model type: {stats['ml_stats']['model_type']}")


def main():
    """Run all tests"""
    print("\n🧪 ML Glossary Selector Tests\n")
    
    try:
        test_ml_selector()
        test_integrated_strategy()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)
        
        print("\n💡 Tips:")
        print("  • Install sentence-transformers for best ML quality:")
        print("    pip install sentence-transformers")
        print("  • ML selector learns from every term selection")
        print("  • Higher confidence = more similar to training data")
        print("  • Falls back to adaptive strategy when confidence is low")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
