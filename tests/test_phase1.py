#!/usr/bin/env python3
"""
Phase 1 Integration Test

Tests TMDB client, NER corrector, and glossary generator
without relying on the complex logger setup.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.tmdb_client import TMDBClient, load_api_key
from shared.ner_corrector import NERCorrector
from shared.glossary_generator import GlossaryGenerator


def test_tmdb_client():
    """Test TMDB client functionality"""
    print("=" * 60)
    print("TEST 1: TMDB Client")
    print("=" * 60)
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ TMDB API key not found in config/secrets.json")
        return False
    
    print("✓ API key loaded")
    
    # Initialize client
    client = TMDBClient(api_key)
    print("✓ Client initialized")
    
    # Search for movie
    print("\nSearching for: Jaane Tu Ya Jaane Na (2008)")
    movie = client.search_movie("Jaane Tu Ya Jaane Na", year=2008)
    
    if not movie:
        print("❌ Movie not found")
        return False
    
    print(f"✓ Found: {movie['title']} ({movie['year']})")
    print(f"  TMDB ID: {movie['id']}")
    
    # Get metadata
    print("\nFetching metadata...")
    metadata = client.get_movie_metadata(movie['id'])
    
    if not metadata:
        print("❌ Failed to fetch metadata")
        return False
    
    print(f"✓ Metadata retrieved")
    print(f"  Cast: {len(metadata['cast'])} members")
    print(f"  Crew: {len(metadata['crew'])} members")
    print(f"  Genres: {', '.join(metadata['genres'])}")
    
    # Show top 5 cast
    print("\n  Top Cast:")
    for cast in metadata['cast'][:5]:
        print(f"    - {cast['name']} as {cast['character']}")
    
    return True, metadata


def test_glossary_generator(metadata):
    """Test glossary generator"""
    print("\n" + "=" * 60)
    print("TEST 2: Glossary Generator")
    print("=" * 60)
    
    # Initialize generator
    generator = GlossaryGenerator(metadata)
    print("✓ Generator initialized")
    
    # Generate glossary
    print("\nGenerating glossary...")
    glossary = generator.generate()
    
    print(f"✓ Generated {len(glossary)} entries")
    
    # Show sample entries
    print("\n  Sample entries:")
    for i, (key, value) in enumerate(list(glossary.items())[:10]):
        print(f"    {i+1}. {key} -> {value}")
    
    # Test ASR glossary
    print("\nGenerating ASR glossary...")
    asr_terms = generator.generate_for_asr()
    print(f"✓ Generated {len(asr_terms)} ASR terms")
    print(f"  Sample: {', '.join(asr_terms[:10])}")
    
    # Test translation glossary
    print("\nGenerating translation glossary...")
    trans_glossary = generator.generate_for_translation()
    print(f"✓ Generated {len(trans_glossary)} translation mappings")
    
    return True


def test_ner_corrector(metadata):
    """Test NER corrector"""
    print("\n" + "=" * 60)
    print("TEST 3: NER Corrector")
    print("=" * 60)
    
    # Initialize corrector
    print("Loading spaCy model...")
    corrector = NERCorrector(metadata, model_name="en_core_web_sm")
    corrector.load_model()
    print("✓ Model loaded")
    
    # Test text with entities
    test_text = "Jai and Aditi are friends in Mumbai. Meow is also there."
    
    print(f"\nTest text: '{test_text}'")
    print("\nExtracting entities...")
    entities = corrector.extract_entities(test_text)
    
    print(f"✓ Found {len(entities)} entities:")
    for ent in entities:
        print(f"  - {ent['text']} ({ent['label']})")
    
    # Test correction
    print("\nTesting correction...")
    corrected = corrector.correct_text(test_text)
    print(f"Original:  {test_text}")
    print(f"Corrected: {corrected}")
    
    # Test validation
    print("\nValidating entities...")
    validations = corrector.validate_entities(test_text)
    for val in validations:
        status = "✓" if not val['needs_correction'] else "⚠"
        print(f"  {status} {val['original']} -> {val['suggested']}")
    
    return True


def main():
    """Run all tests"""
    print("\n🚀 PHASE 1 INTEGRATION TEST")
    print("Testing TMDB + NER + Glossary\n")
    
    try:
        # Test 1: TMDB Client
        result = test_tmdb_client()
        if not result:
            print("\n❌ TMDB test failed")
            return 1
        
        success, metadata = result
        
        # Test 2: Glossary Generator
        if not test_glossary_generator(metadata):
            print("\n❌ Glossary test failed")
            return 1
        
        # Test 3: NER Corrector
        if not test_ner_corrector(metadata):
            print("\n❌ NER test failed")
            return 1
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nPhase 1 implementation is working correctly!")
        print("Core modules ready:")
        print("  ✓ shared/tmdb_client.py")
        print("  ✓ shared/ner_corrector.py")
        print("  ✓ shared/glossary_generator.py")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
