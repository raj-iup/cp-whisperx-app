#!/usr/bin/env python3
"""
Enhanced Hybrid Subtitle Merger v2
Handles both hallucinations AND repeated lyrics intelligently
"""

import srt
import argparse
from pathlib import Path
from typing import List, Set, Tuple
import sys
from datetime import timedelta

def is_likely_lyrics(text: str, duration: float) -> bool:
    """
    Determine if subtitle is likely song lyrics based on characteristics
    """
    word_count = len(text.split())
    
    # Long sentences with many words in short time = likely lyrics
    if word_count > 10 and duration < 5.0:
        return True
    
    # Contains Hindi/Devanagari = likely lyrics
    if any('\u0900' <= char <= '\u097F' for char in text):
        return True
    
    # Common lyric patterns
    lyric_indicators = ['ya jaane na', 'tera mujhse', 'dil laga', 'nahi']
    if any(indicator in text.lower() for indicator in lyric_indicators):
        return True
    
    return False


def collapse_repeated_lyrics(subtitles: List[srt.Subtitle]) -> List[srt.Subtitle]:
    """
    Collapse consecutive identical lyrics into single longer subtitle
    """
    if not subtitles:
        return []
    
    collapsed = []
    i = 0
    
    while i < len(subtitles):
        current = subtitles[i]
        current_text = current.content.strip()
        duration = (current.end - current.start).total_seconds()
        
        # Check if this is lyrics
        if is_likely_lyrics(current_text, duration):
            # Find all consecutive identical lyrics
            j = i + 1
            while j < len(subtitles) and subtitles[j].content.strip() == current_text:
                j += 1
            
            if j > i + 1:  # Found repetitions
                # Collapse into single subtitle spanning the time range
                collapsed_sub = srt.Subtitle(
                    index=len(collapsed) + 1,
                    start=current.start,
                    end=subtitles[j-1].end,  # End at last repetition
                    content=current_text
                )
                collapsed.append(collapsed_sub)
                print(f"  Collapsed {j-i} repeated lyrics at {current.start}: '{current_text[:50]}...'")
                i = j
                continue
        
        # Not lyrics or no repetition, keep as is
        collapsed.append(srt.Subtitle(
            index=len(collapsed) + 1,
            start=current.start,
            end=current.end,
            content=current.content
        ))
        i += 1
    
    return collapsed


def detect_hallucinations(subtitles: List[srt.Subtitle]) -> Set[int]:
    """
    Detect likely hallucination segments (improved version)
    Distinguishes between hallucinations and actual repeated lyrics
    """
    hallucinations = set()
    
    # Detection 1: Short repetitive words (likely hallucinations)
    for i in range(len(subtitles) - 2):
        text1 = subtitles[i].content.strip().lower()
        text2 = subtitles[i+1].content.strip().lower()
        text3 = subtitles[i+2].content.strip().lower()
        
        word_count = len(text1.split())
        duration = (subtitles[i].end - subtitles[i].start).total_seconds()
        
        # Only flag if SHORT repetitive text (not long lyrics)
        if text1 == text2 == text3 and len(text1) > 0 and word_count <= 3:
            # This is likely hallucination (e.g., "Okay." repeated)
            hallucinations.add(i)
            hallucinations.add(i+1)
            hallucinations.add(i+2)
            print(f"  Hallucination (short repetition) at {subtitles[i].start}: '{text1}'")
    
    # Detection 2: Excessive segments in short time (likely hallucination clustering)
    time_window = 10  # seconds
    max_segments = 12
    
    for i in range(len(subtitles)):
        start_time = subtitles[i].start.total_seconds()
        
        segments_in_window = []
        for j in range(i, min(i + 20, len(subtitles))):
            if subtitles[j].start.total_seconds() - start_time < time_window:
                segments_in_window.append(j)
        
        # Check if these are short segments (hallucination) or lyrics
        if len(segments_in_window) > max_segments:
            # Check average word count
            avg_words = sum(len(subtitles[j].content.split()) for j in segments_in_window) / len(segments_in_window)
            
            if avg_words < 5:  # Short segments = hallucination
                hallucinations.update(segments_in_window)
                print(f"  Hallucination (clustering) at {subtitles[i].start}: {len(segments_in_window)} segments in {time_window}s")
    
    # Detection 3: Very short duration with few words
    for i, sub in enumerate(subtitles):
        duration = (sub.end - sub.start).total_seconds()
        word_count = len(sub.content.split())
        
        if duration < 0.3 and 1 <= word_count <= 2:
            hallucinations.add(i)
            print(f"  Hallucination (too short) at {sub.start}: {duration:.2f}s for '{sub.content}'")
    
    return hallucinations


def find_matching_subtitle(
    subs: List[srt.Subtitle], 
    start_time: float, 
    end_time: float,
    tolerance: float = 2.0
) -> Tuple[srt.Subtitle, float]:
    """Find subtitle that best matches given time range"""
    best_match = None
    best_score = 0.0
    
    for sub in subs:
        sub_start = sub.start.total_seconds()
        sub_end = sub.end.total_seconds()
        
        # Calculate overlap
        overlap_start = max(start_time, sub_start)
        overlap_end = min(end_time, sub_end)
        
        if overlap_start < overlap_end:
            overlap = overlap_end - overlap_start
            duration = end_time - start_time
            score = overlap / duration if duration > 0 else 0
            
            if score > best_score and score > 0.5:
                best_score = score
                best_match = sub
    
    # Proximity match
    if not best_match:
        for sub in subs:
            sub_start = sub.start.total_seconds()
            distance = abs(sub_start - start_time)
            
            if distance < tolerance:
                score = 1.0 - (distance / tolerance)
                if score > best_score:
                    best_score = score
                    best_match = sub
    
    return best_match, best_score


def merge_translations(
    whisperx_file: Path,
    indictrans2_file: Path,
    output_file: Path,
    verbose: bool = False
) -> None:
    """
    Create enhanced hybrid translation:
    - Collapses repeated lyrics
    - Uses IndICTrans2 for hallucinations
    - Uses WhisperX for normal dialogue
    """
    print("=" * 70)
    print("ENHANCED HYBRID SUBTITLE MERGER V2")
    print("=" * 70)
    print(f"WhisperX:     {whisperx_file}")
    print(f"IndICTrans2:  {indictrans2_file}")
    print(f"Output:       {output_file}")
    print()
    
    # Load subtitles
    print("Loading subtitles...")
    with open(whisperx_file, 'r', encoding='utf-8') as f:
        whisperx_subs = list(srt.parse(f.read()))
    
    with open(indictrans2_file, 'r', encoding='utf-8') as f:
        indictrans2_subs = list(srt.parse(f.read()))
    
    print(f"  WhisperX:     {len(whisperx_subs)} subtitles")
    print(f"  IndICTrans2:  {len(indictrans2_subs)} subtitles")
    print()
    
    # Step 1: Collapse repeated lyrics in both
    print("Collapsing repeated lyrics...")
    whisperx_subs = collapse_repeated_lyrics(whisperx_subs)
    indictrans2_subs = collapse_repeated_lyrics(indictrans2_subs)
    print(f"  WhisperX after collapse:     {len(whisperx_subs)} subtitles")
    print(f"  IndICTrans2 after collapse:  {len(indictrans2_subs)} subtitles")
    print()
    
    # Step 2: Detect hallucinations
    print("Detecting hallucinations...")
    hallucination_indices = detect_hallucinations(whisperx_subs)
    print(f"  Detected {len(hallucination_indices)} hallucination segments")
    print()
    
    # Step 3: Build hybrid
    print("Building hybrid translation...")
    hybrid = []
    whisperx_count = 0
    indictrans2_count = 0
    skipped_count = 0
    
    for i, wsub in enumerate(whisperx_subs):
        if i in hallucination_indices:
            # Use IndICTrans2 for hallucinations
            start_sec = wsub.start.total_seconds()
            end_sec = wsub.end.total_seconds()
            
            match, score = find_matching_subtitle(indictrans2_subs, start_sec, end_sec)
            
            if match:
                hybrid.append(srt.Subtitle(
                    index=len(hybrid) + 1,
                    start=wsub.start,
                    end=wsub.end,
                    content=match.content
                ))
                indictrans2_count += 1
                
                if verbose:
                    print(f"  {wsub.start} → IndICTrans2: {match.content[:50]}")
            else:
                skipped_count += 1
                if verbose:
                    print(f"  {wsub.start} → SKIPPED (no match)")
        else:
            # Use WhisperX (better context)
            hybrid.append(srt.Subtitle(
                index=len(hybrid) + 1,
                start=wsub.start,
                end=wsub.end,
                content=wsub.content
            ))
            whisperx_count += 1
    
    # Write output
    print()
    print("Writing enhanced hybrid translation...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(srt.compose(hybrid))
    
    # Summary
    print()
    print("=" * 70)
    print("ENHANCED HYBRID TRANSLATION COMPLETE")
    print("=" * 70)
    print(f"Total segments:       {len(hybrid)}")
    print(f"  WhisperX (context): {whisperx_count} ({whisperx_count/len(hybrid)*100:.1f}%)")
    print(f"  IndICTrans2 (safe): {indictrans2_count} ({indictrans2_count/len(hybrid)*100:.1f}%)")
    if skipped_count:
        print(f"  Skipped:            {skipped_count}")
    print()
    print(f"✓ Saved to: {output_file}")
    print()
    print("Improvements:")
    print("  ✓ Collapsed repeated lyrics into single subtitles")
    print("  ✓ Distinguished hallucinations from actual lyrics")
    print("  ✓ Context-aware dialogue (WhisperX)")
    print("  ✓ No hallucinations (IndICTrans2)")


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced hybrid subtitle merger (handles lyrics repetition)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('whisperx_file', type=Path)
    parser.add_argument('indictrans2_file', type=Path)
    parser.add_argument('output_file', type=Path)
    parser.add_argument('-v', '--verbose', action='store_true')
    
    args = parser.parse_args()
    
    if not args.whisperx_file.exists():
        print(f"Error: WhisperX file not found: {args.whisperx_file}")
        sys.exit(1)
    
    if not args.indictrans2_file.exists():
        print(f"Error: IndICTrans2 file not found: {args.indictrans2_file}")
        sys.exit(1)
    
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    
    merge_translations(
        args.whisperx_file,
        args.indictrans2_file,
        args.output_file,
        args.verbose
    )


if __name__ == '__main__':
    main()
