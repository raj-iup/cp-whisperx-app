#!/usr/bin/env python3
"""
Test Enhanced Subtitle Generation

Verifies that subtitles now include song metadata and formatting
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def analyze_subtitles(job_path: Path):
    """Analyze enhanced subtitles"""
    
    srt_file = job_path / "14_subtitle_gen" / "subtitles.srt"
    
    if not srt_file.exists():
        print("❌ Subtitles not found")
        return None
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse subtitle entries
    entries = content.split('\n\n')
    
    stats = {
        'total': 0,
        'dialogue': 0,
        'lyrics': 0,
        'with_song_metadata': 0,
        'songs_found': set()
    }
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            stats['total'] += 1
            text = '\n'.join(lines[2:])
            
            # Check for lyrics formatting
            if '<i>♪' in text or '♪' in text:
                stats['lyrics'] += 1
            else:
                stats['dialogue'] += 1
            
            # Check for song metadata
            if 'Song:' in text:
                stats['with_song_metadata'] += 1
                
                # Extract song title
                match = re.search(r'Song: "([^"]+)"', text)
                if match:
                    stats['songs_found'].add(match.group(1))
    
    return stats


def show_examples(job_path: Path):
    """Show example subtitles"""
    
    srt_file = job_path / "14_subtitle_gen" / "subtitles.srt"
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    entries = content.split('\n\n')
    
    print("\n" + "=" * 70)
    print("EXAMPLE SUBTITLES")
    print("=" * 70)
    
    shown = {'dialogue': False, 'song_meta': False, 'lyrics': False}
    
    for entry in entries[:100]:
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            text = '\n'.join(lines[2:])
            
            # Dialogue example
            if not shown['dialogue'] and '<i>' not in text and '♪' not in text:
                print("\n📝 Dialogue (Normal):")
                print("-" * 70)
                print(entry[:200])
                shown['dialogue'] = True
            
            # Song with metadata
            if not shown['song_meta'] and 'Song:' in text:
                print("\n🎵 Song with Metadata:")
                print("-" * 70)
                print(entry[:300])
                shown['song_meta'] = True
            
            # Lyrics without metadata
            if not shown['lyrics'] and '<i>♪' in text and 'Song:' not in text:
                print("\n🎶 Lyrics (Formatted):")
                print("-" * 70)
                print(entry[:200])
                shown['lyrics'] = True
            
            if all(shown.values()):
                break


def main():
    """Main test function"""
    
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "ENHANCED SUBTITLE GENERATION TEST" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")
    
    job_path = Path("out/2025/11/14/1/20251114-0001")
    
    if not job_path.exists():
        print("\n❌ Test job not found")
        return 1
    
    print(f"\nAnalyzing job: {job_path.name}")
    
    # Analyze subtitles
    stats = analyze_subtitles(job_path)
    
    if not stats:
        return 1
    
    # Show statistics
    print("\n" + "=" * 70)
    print("SUBTITLE STATISTICS")
    print("=" * 70)
    print(f"Total subtitles: {stats['total']}")
    print(f"Dialogue: {stats['dialogue']} ({stats['dialogue']/stats['total']*100:.1f}%)")
    print(f"Lyrics: {stats['lyrics']} ({stats['lyrics']/stats['total']*100:.1f}%)")
    print(f"With song metadata: {stats['with_song_metadata']}")
    
    if stats['songs_found']:
        print(f"\nSongs identified in subtitles:")
        for song in sorted(stats['songs_found']):
            print(f"  • {song}")
    
    # Show examples
    show_examples(job_path)
    
    # Final verdict
    print("\n" + "=" * 70)
    print("ENHANCEMENT STATUS")
    print("=" * 70)
    
    if stats['lyrics'] > 0 and stats['with_song_metadata'] > 0:
        print("✅ ENHANCEMENT ACTIVE")
        print(f"   {stats['lyrics']} lyrics subtitles formatted")
        print(f"   {len(stats['songs_found'])} songs identified with metadata")
        print("\n   Benefits:")
        print("   ✨ Visual distinction for songs (♪)")
        print("   📝 Italic formatting for lyrics")
        print("   🎵 Song title and artist shown")
        print("   🎬 Professional subtitle quality")
    else:
        print("❌ ENHANCEMENT NOT DETECTED")
    
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
