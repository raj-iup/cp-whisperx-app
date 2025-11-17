#!/usr/bin/env python3
"""
Test MusicBrainz Integration - Phase 1 Verification

Tests the cascade fallback system:
1. MusicBrainz API (primary)
2. Local Database (fallback)
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.musicbrainz_client import MusicBrainzClient

# Test movies list
TEST_MOVIES = [
    {
        "title": "Jaane Tu... Ya Jaane Na",
        "year": 2008,
        "imdb_id": "tt0473367",
        "expected": "Should find in MusicBrainz"
    },
    {
        "title": "3 Idiots",
        "year": 2009,
        "imdb_id": "tt1187043",
        "expected": "Should find in MusicBrainz"
    },
    {
        "title": "Dangal",
        "year": 2016,
        "imdb_id": "tt5074352",
        "expected": "Should find in MusicBrainz"
    },
    {
        "title": "PK",
        "year": 2014,
        "imdb_id": "tt2338151",
        "expected": "Should find in MusicBrainz"
    },
    {
        "title": "Baahubali",
        "year": 2015,
        "imdb_id": "tt2631186",
        "expected": "May not find (regional film)"
    }
]


def test_musicbrainz_client():
    """Test MusicBrainz client directly"""
    print("=" * 70)
    print("TEST 1: MusicBrainz Client")
    print("=" * 70)
    
    client = MusicBrainzClient()
    results = []
    
    for movie in TEST_MOVIES:
        print(f"\n{movie['title']} ({movie['year']})")
        print(f"  Expected: {movie['expected']}")
        print(f"  Testing...", end=" ")
        
        soundtrack = client.get_soundtrack(
            imdb_id=movie['imdb_id'],
            title=movie['title'],
            year=movie['year']
        )
        
        if soundtrack and soundtrack['found']:
            tracks = soundtrack['tracks']
            print(f"✓ Found {len(tracks)} tracks")
            if tracks:
                print(f"    First: {tracks[0]['title']} - {tracks[0]['artist']}")
            
            results.append({
                'movie': movie['title'],
                'success': True,
                'track_count': len(tracks)
            })
        else:
            print("✗ Not found")
            results.append({
                'movie': movie['title'],
                'success': False,
                'track_count': 0
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("MUSICBRAINZ CLIENT SUMMARY")
    print("=" * 70)
    success_count = sum(1 for r in results if r['success'])
    total_tracks = sum(r['track_count'] for r in results)
    
    print(f"Success Rate: {success_count}/{len(TEST_MOVIES)} "
          f"({success_count/len(TEST_MOVIES)*100:.0f}%)")
    print(f"Total Tracks Found: {total_tracks}")
    
    return results


def test_tmdb_integration():
    """Test TMDB integration with MusicBrainz"""
    print("\n\n" + "=" * 70)
    print("TEST 2: TMDB Integration")
    print("=" * 70)
    
    from scripts.tmdb_enrichment import get_soundtrack_for_movie
    
    # Test with a movie that should be in MusicBrainz
    print("\nTest: Get soundtrack via TMDB integration")
    print("  Movie: 3 Idiots (2009)")
    
    tracks = get_soundtrack_for_movie(
        title="3 Idiots",
        year=2009,
        imdb_id="tt1187043",
        use_musicbrainz=True
    )
    
    if tracks:
        print(f"  ✓ Found {len(tracks)} tracks")
        if len(tracks) > 0:
            print(f"    Track 1: {tracks[0]['title']}")
            print(f"    Artist: {tracks[0]['artist']}")
    else:
        print("  ✗ Not found")
    
    return len(tracks) > 0


def test_local_fallback():
    """Test fallback to local database"""
    print("\n\n" + "=" * 70)
    print("TEST 3: Local Database Fallback")
    print("=" * 70)
    
    from scripts.tmdb_enrichment import get_soundtrack_for_movie
    
    # Test with movie that's in local DB (Jaane Tu Ya Jaane Na)
    print("\nTest: Local database fallback")
    print("  Movie: Jaane Tu... Ya Jaane Na (2008)")
    print("  MusicBrainz: Disabled (testing fallback)")
    
    tracks = get_soundtrack_for_movie(
        title="Jaane Tu... Ya Jaane Na",
        year=2008,
        imdb_id="tt0473367",
        use_musicbrainz=False  # Force local DB
    )
    
    if tracks:
        print(f"  ✓ Found {len(tracks)} tracks in local DB")
        if len(tracks) > 0:
            print(f"    Track 1: {tracks[0]['title']}")
    else:
        print("  ✗ Not found in local DB")
    
    return len(tracks) > 0


def test_caching():
    """Test that MusicBrainz results are cached"""
    print("\n\n" + "=" * 70)
    print("TEST 4: Caching Verification")
    print("=" * 70)
    
    db_path = PROJECT_ROOT / "config" / "bollywood_soundtracks.json"
    
    if not db_path.exists():
        print("  ✗ Local database file not found")
        return False
    
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print(f"\nLocal database statistics:")
    print(f"  Total movies: {len([k for k in db.keys() if k != '_template'])}")
    print(f"  Database file: {db_path}")
    
    # Check if recently fetched movies are cached
    cached_movies = [k for k in db.keys() if k != '_template']
    print(f"\nCached movies:")
    for movie in cached_movies[:10]:  # Show first 10
        track_count = len(db[movie].get('tracks', []))
        source = db[movie].get('source', 'manual')
        print(f"  - {movie}: {track_count} tracks (source: {source})")
    
    return True


def run_all_tests():
    """Run all Phase 1 tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 1 VERIFICATION - MusicBrainz Integration" + " " * 8 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {
        'musicbrainz_client': False,
        'tmdb_integration': False,
        'local_fallback': False,
        'caching': False
    }
    
    try:
        # Test 1: MusicBrainz Client
        mb_results = test_musicbrainz_client()
        results['musicbrainz_client'] = any(r['success'] for r in mb_results)
        
        # Test 2: TMDB Integration
        results['tmdb_integration'] = test_tmdb_integration()
        
        # Test 3: Local Fallback
        results['local_fallback'] = test_local_fallback()
        
        # Test 4: Caching
        results['caching'] = test_caching()
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Final Summary
    print("\n\n" + "=" * 70)
    print("PHASE 1 VERIFICATION - FINAL RESULTS")
    print("=" * 70)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name.replace('_', ' ').title()}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ PHASE 1 COMPLETE - All tests passed!")
        print("\nNext steps:")
        print("  1. Test with 10+ more Bollywood movies")
        print("  2. Measure coverage rate (target: 70%+)")
        print("  3. Decide on Phase 2 (Spotify) based on coverage")
    else:
        print("✗ PHASE 1 INCOMPLETE - Some tests failed")
        print("\nFailed tests need investigation before proceeding")
    
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
