#!/usr/bin/env python3
"""
Cache Management Utility

Manage TMDB and MusicBrainz caches:
- View cache statistics
- Clear expired entries
- Clear all caches
- Clear specific cache types
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.tmdb_cache import TMDBCache
from shared.musicbrainz_cache import MusicBrainzCache


def print_stats(cache_type: str, stats: dict):
    """Print cache statistics in a nice format"""
    print(f"\n{'='*60}")
    print(f"{cache_type.upper()} CACHE STATISTICS")
    print(f"{'='*60}")
    
    for key, value in stats.items():
        formatted_key = key.replace('_', ' ').title()
        print(f"  {formatted_key:25s}: {value}")
    
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage TMDB and MusicBrainz API caches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View all cache statistics
  python cache_manager.py --stats
  
  # Clear expired entries only
  python cache_manager.py --clear-expired
  
  # Clear all TMDB cache
  python cache_manager.py --clear-tmdb
  
  # Clear all MusicBrainz cache
  python cache_manager.py --clear-musicbrainz
  
  # Clear everything
  python cache_manager.py --clear-all
  
  # Clear specific TMDB entry
  python cache_manager.py --clear-tmdb --id 14467
  
  # Clear specific MusicBrainz entry
  python cache_manager.py --clear-musicbrainz --id abc123-def456
        """
    )
    
    parser.add_argument('--stats', action='store_true',
                       help='Show cache statistics')
    parser.add_argument('--clear-expired', action='store_true',
                       help='Clear expired cache entries')
    parser.add_argument('--clear-all', action='store_true',
                       help='Clear all caches')
    parser.add_argument('--clear-tmdb', action='store_true',
                       help='Clear TMDB cache')
    parser.add_argument('--clear-musicbrainz', action='store_true',
                       help='Clear MusicBrainz cache')
    parser.add_argument('--id', type=str,
                       help='Specific cache entry ID to clear')
    parser.add_argument('--cache-dir', type=Path,
                       help='Custom cache directory (default: out/)')
    
    args = parser.parse_args()
    
    # Default to showing stats if no action specified
    if not any([args.stats, args.clear_expired, args.clear_all, 
                args.clear_tmdb, args.clear_musicbrainz]):
        args.stats = True
    
    # Determine cache directories
    if args.cache_dir:
        tmdb_cache_dir = args.cache_dir / "tmdb_cache"
        mb_cache_dir = args.cache_dir / "musicbrainz_cache"
    else:
        tmdb_cache_dir = PROJECT_ROOT / "out" / "tmdb_cache"
        mb_cache_dir = PROJECT_ROOT / "out" / "musicbrainz_cache"
    
    # Initialize caches
    tmdb_cache = TMDBCache(cache_dir=tmdb_cache_dir)
    mb_cache = MusicBrainzCache(cache_dir=mb_cache_dir)
    
    # Show statistics
    if args.stats:
        tmdb_stats = tmdb_cache.get_stats()
        mb_stats = mb_cache.get_stats()
        
        print_stats("TMDB", tmdb_stats)
        print_stats("MusicBrainz", mb_stats)
        
        # Calculate totals
        print(f"\n{'='*60}")
        print("COMBINED STATISTICS")
        print(f"{'='*60}")
        print(f"  Total Cached Items:       {tmdb_stats['total_entries'] + mb_stats['total_releases']}")
        print(f"  MusicBrainz Search Cache: {mb_stats['total_searches']}")
        print(f"{'='*60}\n")
    
    # Clear expired entries
    if args.clear_expired:
        print("\nClearing expired cache entries...")
        tmdb_cache.clear_expired()
        mb_cache.clear_expired()
        print("✓ Expired entries cleared\n")
        
        # Show updated stats
        tmdb_stats = tmdb_cache.get_stats()
        mb_stats = mb_cache.get_stats()
        print(f"  TMDB entries remaining:        {tmdb_stats['total_entries']}")
        print(f"  MusicBrainz entries remaining: {mb_stats['total_releases']}")
        print()
    
    # Clear all caches
    if args.clear_all:
        print("\nClearing ALL caches...")
        confirm = input("Are you sure? This will delete all cached data. (yes/no): ")
        if confirm.lower() == 'yes':
            tmdb_cache.clear()
            mb_cache.clear()
            print("✓ All caches cleared\n")
        else:
            print("Cancelled\n")
    
    # Clear TMDB cache
    if args.clear_tmdb and not args.clear_all:
        if args.id:
            print(f"\nClearing TMDB cache entry: {args.id}")
            try:
                tmdb_cache.clear(int(args.id))
                print(f"✓ Cleared TMDB cache for ID: {args.id}\n")
            except ValueError:
                print(f"Error: Invalid TMDB ID '{args.id}' (must be numeric)\n")
        else:
            print("\nClearing entire TMDB cache...")
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() == 'yes':
                tmdb_cache.clear()
                print("✓ TMDB cache cleared\n")
            else:
                print("Cancelled\n")
    
    # Clear MusicBrainz cache
    if args.clear_musicbrainz and not args.clear_all:
        if args.id:
            print(f"\nClearing MusicBrainz cache entry: {args.id}")
            mb_cache.clear(args.id)
            print(f"✓ Cleared MusicBrainz cache for ID: {args.id}\n")
        else:
            print("\nClearing entire MusicBrainz cache...")
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() == 'yes':
                mb_cache.clear()
                print("✓ MusicBrainz cache cleared\n")
            else:
                print("Cancelled\n")


if __name__ == '__main__':
    main()
