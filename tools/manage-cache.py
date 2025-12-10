#!/usr/bin/env python3
"""
Cache management CLI tool for AD-014 multi-phase subtitle workflow.

Provides commands to inspect, manage, and clear cached baseline artifacts.

Usage:
    ./tools/manage-cache.py stats                  # Show cache statistics
    ./tools/manage-cache.py list                   # List cached media
    ./tools/manage-cache.py info <media_id>        # Show info for specific media
    ./tools/manage-cache.py clear <media_id>       # Clear specific media cache
    ./tools/manage-cache.py clear --all            # Clear all cache (WARNING!)
    ./tools/manage-cache.py verify <media_file>    # Verify cache for media file

Architecture Decision: AD-014 (Multi-Phase Subtitle Workflow)
"""
# Standard library
import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.media_identity import compute_media_id, verify_media_id_stability
from shared.cache_manager import MediaCacheManager
from shared.logger import get_logger

logger = get_logger(__name__)


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp as human-readable."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return iso_timestamp


def cmd_stats(args):
    """Show cache statistics."""
    cache_mgr = MediaCacheManager()
    
    print("=" * 80)
    print("CACHE STATISTICS")
    print("=" * 80)
    
    # Total cache size
    total_size = cache_mgr.get_cache_size()
    print(f"\n📊 Total cache size: {format_size(total_size)}")
    
    # Count cached media
    cached_media = cache_mgr.list_cached_media()
    print(f"📂 Cached media files: {len(cached_media)}")
    
    # Cache location
    print(f"📁 Cache location: {cache_mgr.cache_root}")
    
    # Show breakdown by media
    if cached_media:
        print("\n" + "=" * 80)
        print("CACHE BREAKDOWN BY MEDIA")
        print("=" * 80)
        
        for media_id in cached_media[:10]:  # Show first 10
            media_size = cache_mgr.get_cache_size(media_id)
            print(f"\n🎬 Media ID: {media_id[:16]}...")
            print(f"   Size: {format_size(media_size)}")
            
            # Load metadata if available
            baseline = cache_mgr.get_baseline(media_id)
            if baseline:
                metadata = baseline.metadata
                print(f"   File: {Path(metadata.get('media_file', 'unknown')).name}")
                print(f"   Created: {format_timestamp(baseline.created_at)}")
                print(f"   Segments: {metadata.get('num_segments', 0)}")
        
        if len(cached_media) > 10:
            print(f"\n... and {len(cached_media) - 10} more")
    
    print("\n" + "=" * 80)


def cmd_list(args):
    """List all cached media."""
    cache_mgr = MediaCacheManager()
    cached_media = cache_mgr.list_cached_media()
    
    if not cached_media:
        print("📭 No cached media found")
        return
    
    print("=" * 80)
    print(f"CACHED MEDIA ({len(cached_media)} files)")
    print("=" * 80)
    
    for i, media_id in enumerate(cached_media, 1):
        baseline = cache_mgr.get_baseline(media_id)
        
        if baseline:
            metadata = baseline.metadata
            filename = Path(metadata.get('media_file', 'unknown')).name
            created = format_timestamp(baseline.created_at)
            segments = metadata.get('num_segments', 0)
            
            print(f"\n{i}. {media_id[:16]}...")
            print(f"   File: {filename}")
            print(f"   Created: {created}")
            print(f"   Segments: {segments}")
        else:
            print(f"\n{i}. {media_id[:16]}... (corrupted)")


def cmd_info(args):
    """Show detailed info for specific media."""
    cache_mgr = MediaCacheManager()
    media_id = args.media_id
    
    baseline = cache_mgr.get_baseline(media_id)
    
    if not baseline:
        print(f"❌ No cache found for media ID: {media_id}")
        return
    
    print("=" * 80)
    print(f"CACHE INFO: {media_id[:16]}...")
    print("=" * 80)
    
    metadata = baseline.metadata
    
    print(f"\n📁 File: {metadata.get('media_file', 'unknown')}")
    print(f"📅 Created: {format_timestamp(baseline.created_at)}")
    print(f"⏱️  Duration: {metadata.get('duration', 0):.1f}s")
    
    print(f"\n📊 BASELINE ARTIFACTS:")
    print(f"   Audio file: {baseline.audio_file}")
    print(f"   ASR segments: {metadata.get('num_segments', 0)}")
    print(f"   Aligned segments: {metadata.get('num_aligned', 0)}")
    print(f"   VAD segments: {metadata.get('num_vad', 0)}")
    
    if metadata.get('has_diarization'):
        print(f"   Diarization: ✅ Available")
    else:
        print(f"   Diarization: ❌ Not available")
    
    # Cache size
    media_size = cache_mgr.get_cache_size(media_id)
    print(f"\n💾 Cache size: {format_size(media_size)}")
    
    # Show sample segments
    if baseline.segments:
        print(f"\n📝 SAMPLE SEGMENTS (first 3):")
        for i, seg in enumerate(baseline.segments[:3], 1):
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            text = seg.get('text', '')[:60]
            print(f"   {i}. [{start:.1f}s - {end:.1f}s] {text}...")
    
    print("\n" + "=" * 80)


def cmd_clear(args):
    """Clear cache for specific media or all cache."""
    cache_mgr = MediaCacheManager()
    
    if args.all:
        print("⚠️  WARNING: This will clear ALL cached media!")
        response = input("Are you sure? Type 'yes' to confirm: ")
        
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        if cache_mgr.clear_all_cache():
            print("✅ All cache cleared successfully")
        else:
            print("❌ Failed to clear cache")
            sys.exit(1)
    
    elif args.media_id:
        media_id = args.media_id
        
        # Verify it exists
        if not cache_mgr.has_baseline(media_id):
            print(f"⚠️  No cache found for media ID: {media_id}")
            return
        
        if cache_mgr.clear_baseline(media_id):
            print(f"✅ Cache cleared for media ID: {media_id[:16]}...")
        else:
            print(f"❌ Failed to clear cache for media ID: {media_id}")
            sys.exit(1)
    
    else:
        print("❌ Must specify either --all or <media_id>")
        sys.exit(1)


def cmd_verify(args):
    """Verify cache for media file."""
    media_file = Path(args.media_file).resolve()
    
    if not media_file.exists():
        print(f"❌ Media file not found: {media_file}")
        sys.exit(1)
    
    print("=" * 80)
    print(f"VERIFYING CACHE FOR: {media_file.name}")
    print("=" * 80)
    
    # Compute media ID
    print("\n🔑 Computing media ID...")
    try:
        media_id = compute_media_id(media_file)
        print(f"✅ Media ID: {media_id[:16]}...")
    except Exception as e:
        print(f"❌ Failed to compute media ID: {e}")
        sys.exit(1)
    
    # Verify stability
    print("\n🔍 Verifying media ID stability...")
    if verify_media_id_stability(media_file, iterations=3):
        print("✅ Media ID is stable across multiple runs")
    else:
        print("⚠️  Warning: Media ID is not stable!")
    
    # Check cache
    cache_mgr = MediaCacheManager()
    print("\n📂 Checking cache...")
    
    if cache_mgr.has_baseline(media_id):
        print("✅ Cached baseline found")
        
        baseline = cache_mgr.get_baseline(media_id)
        if baseline:
            metadata = baseline.metadata
            print(f"   Created: {format_timestamp(baseline.created_at)}")
            print(f"   Segments: {metadata.get('num_segments', 0)}")
            print(f"   Size: {format_size(cache_mgr.get_cache_size(media_id))}")
        else:
            print("⚠️  Warning: Baseline exists but failed to load (corrupted?)")
    else:
        print("📭 No cached baseline found")
        print("   First run will generate and cache baseline")
        print("   Subsequent runs will be 70-80% faster!")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cache management for AD-014 multi-phase subtitle workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # list command
    subparsers.add_parser('list', help='List all cached media')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Show info for specific media')
    info_parser.add_argument('media_id', help='Media ID to inspect')
    
    # clear command
    clear_parser = subparsers.add_parser('clear', help='Clear cache')
    clear_parser.add_argument('media_id', nargs='?', help='Media ID to clear')
    clear_parser.add_argument('--all', action='store_true', help='Clear all cache')
    
    # verify command
    verify_parser = subparsers.add_parser('verify', help='Verify cache for media file')
    verify_parser.add_argument('media_file', help='Path to media file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    commands = {
        'stats': cmd_stats,
        'list': cmd_list,
        'info': cmd_info,
        'clear': cmd_clear,
        'verify': cmd_verify
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
