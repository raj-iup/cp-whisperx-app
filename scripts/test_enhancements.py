#!/usr/bin/env python3
"""
Test script for Priority 1 enhancements:
1. TMDB Soundtrack Fetching with MusicBrainz
2. Auto-enable Song Bias for Bollywood
3. Centralized Data Loaders
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.tmdb_loader import TMDBLoader
from shared.bias_registry import BiasRegistry
from shared.logger import PipelineLogger


def test_tmdb_loader(output_base: Path):
    """Test TMDB loader functionality"""
    print("\n" + "="*70)
    print("TEST 1: TMDB Loader")
    print("="*70)
    
    # Use simple logger without file
    loader = TMDBLoader(output_base, logger=None)
    
    # Load data
    data = loader.load()
    
    print(f"\nTMDB Data Found: {data.found}")
    if data.found:
        print(f"Title: {data.title} ({data.year})")
        print(f"Genres: {', '.join(data.genres[:5])}")
        print(f"Cast: {len(data.cast)} members")
        print(f"Crew: {len(data.crew)} members")
        print(f"Soundtrack: {len(data.soundtrack)} songs")
        
        if data.soundtrack:
            print("\nFirst 3 songs:")
            for i, song in enumerate(data.soundtrack[:3], 1):
                print(f"  {i}. {song.get('title', 'Unknown')} - {song.get('artist', 'Unknown')}")
        
        print(f"\nIs Bollywood: {loader.is_bollywood()}")
        print(f"Should Enable Song Bias: {loader.should_enable_song_bias()}")
    else:
        print("No TMDB data available")
    
    return data.found


def test_bias_registry(output_base: Path):
    """Test bias registry functionality"""
    print("\n" + "="*70)
    print("TEST 2: Bias Registry")
    print("="*70)
    
    registry = BiasRegistry(output_base, logger=None)
    
    # Load all terms
    terms = registry.load()
    counts = terms.count()
    
    print("\nBias Terms Summary:")
    print(f"  Cast names: {counts['cast']}")
    print(f"  Crew names: {counts['crew']}")
    print(f"  Song titles: {counts['songs']}")
    print(f"  Artists: {counts['artists']}")
    print(f"  Composers: {counts['composers']}")
    print(f"  Glossary: {counts['glossary']}")
    print(f"\nTotal character bias: {counts['total_character']}")
    print(f"Total song bias: {counts['total_song']}")
    print(f"Total all terms: {counts['total_all']}")
    
    # Test stage-specific terms
    print("\nStage-specific bias terms:")
    
    asr_terms = registry.get_for_stage('asr')
    print(f"  ASR stage: {len(asr_terms)} terms")
    if asr_terms:
        print(f"    First 5: {', '.join(asr_terms[:5])}")
    
    song_terms = registry.get_for_stage('song_bias_injection')
    print(f"  Song Bias stage: {len(song_terms)} terms")
    if song_terms:
        print(f"    First 5: {', '.join(song_terms[:5])}")
    
    return counts['total_all'] > 0


def test_musicbrainz_integration():
    """Test MusicBrainz client"""
    print("\n" + "="*70)
    print("TEST 3: MusicBrainz Integration")
    print("="*70)
    
    try:
        from scripts.musicbrainz_client import MusicBrainzClient
        
        client = MusicBrainzClient(logger=None)
        
        # Test with a known Bollywood movie
        test_movie = {
            'title': 'Jaane Tu Ya Jaane Na',
            'year': 2008,
            'imdb_id': 'tt0473367'
        }
        
        print(f"\nTesting with: {test_movie['title']} ({test_movie['year']})")
        print("Querying MusicBrainz...")
        
        result = client.get_soundtrack(
            imdb_id=test_movie['imdb_id'],
            title=test_movie['title'],
            year=test_movie['year']
        )
        
        if result and result.get('found'):
            tracks = result.get('tracks', [])
            print(f"✓ Found {len(tracks)} tracks")
            
            if tracks:
                print("\nFirst 3 tracks:")
                for i, track in enumerate(tracks[:3], 1):
                    print(f"  {i}. {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}")
            
            return True
        else:
            print("✗ No soundtrack found in MusicBrainz")
            print("This is expected if the movie isn't in MusicBrainz database")
            return False
    
    except ImportError as e:
        print(f"✗ MusicBrainz client not available: {e}")
        print("Install with: pip install musicbrainzngs")
        return False
    except Exception as e:
        print(f"✗ MusicBrainz test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PRIORITY 1 ENHANCEMENTS - TEST SUITE")
    print("="*70)
    
    # Get output directory from command line or use default
    if len(sys.argv) > 1:
        output_base = Path(sys.argv[1])
    else:
        # Find most recent output directory
        out_dir = PROJECT_ROOT / "out"
        if not out_dir.exists():
            print("\nERROR: No output directory found")
            print("Usage: python test_enhancements.py [output_base]")
            return 1
        
        # Find most recent job
        year_dirs = sorted([d for d in out_dir.iterdir() if d.is_dir()], reverse=True)
        if not year_dirs:
            print("\nERROR: No output directories found in out/")
            return 1
        
        month_dirs = sorted([d for d in year_dirs[0].iterdir() if d.is_dir()], reverse=True)
        if not month_dirs:
            print(f"\nERROR: No output in {year_dirs[0]}")
            return 1
        
        day_dirs = sorted([d for d in month_dirs[0].iterdir() if d.is_dir()], reverse=True)
        if not day_dirs:
            print(f"\nERROR: No output in {month_dirs[0]}")
            return 1
        
        sequence_dirs = sorted([d for d in day_dirs[0].iterdir() if d.is_dir()], reverse=True)
        if not sequence_dirs:
            print(f"\nERROR: No output in {day_dirs[0]}")
            return 1
        
        job_dirs = sorted([d for d in sequence_dirs[0].iterdir() if d.is_dir()], reverse=True)
        if not job_dirs:
            print(f"\nERROR: No jobs in {sequence_dirs[0]}")
            return 1
        
        output_base = job_dirs[0]
    
    print(f"\nTesting with output base: {output_base}")
    
    # Run tests
    results = {
        'tmdb_loader': test_tmdb_loader(output_base),
        'bias_registry': test_bias_registry(output_base),
        'musicbrainz': test_musicbrainz_integration()
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
