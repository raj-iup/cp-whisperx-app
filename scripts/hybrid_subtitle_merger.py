#!/usr/bin/env python3
"""

logger = get_logger(__name__)

Hybrid Subtitle Merger
Combines WhisperX (context-aware) and IndICTrans2 (safe) translations
Uses IndICTrans2 for detected hallucination segments, WhisperX for the rest
"""

# Standard library
import argparse
from pathlib import Path
from typing import List, Set, Tuple
import sys

# Third-party
import srt

# Local
from shared.logger import get_logger

def detect_hallucinations(subtitles: List[srt.Subtitle]) -> Set[int]:
    """
    Detect likely hallucination segments in subtitles
    
    Returns: Set of indices that are likely hallucinations
    """
    hallucinations = set()
    
    # Detection 1: Repetitive text (3+ consecutive identical)
    for i in range(len(subtitles) - 2):
        text1 = subtitles[i].content.strip().lower()
        text2 = subtitles[i+1].content.strip().lower()
        text3 = subtitles[i+2].content.strip().lower()
        
        if text1 == text2 == text3 and len(text1) > 0:
            hallucinations.add(i)
            hallucinations.add(i+1)
            hallucinations.add(i+2)
            logger.info(f"  Repetition detected at {subtitles[i].start}: '{text1}'")
    
    # Detection 2: Excessive segments in short time window
    time_window = 10  # seconds
    max_segments = 12
    
    for i in range(len(subtitles)):
        start_time = subtitles[i].start.total_seconds()
        
        # Count segments within time window
        segments_in_window = []
        for j in range(i, min(i + 20, len(subtitles))):
            if subtitles[j].start.total_seconds() - start_time < time_window:
                segments_in_window.append(j)
        
        if len(segments_in_window) > max_segments:
            hallucinations.update(segments_in_window)
            logger.info(f"  Excessive segments at {subtitles[i].start}: {len(segments_in_window)} in {time_window}s")
    
    # Detection 3: Very short duration with text
    for i, sub in enumerate(subtitles):
        duration = (sub.end - sub.start).total_seconds()
        word_count = len(sub.content.split())
        
        # If duration < 0.3s but has 2+ words, likely hallucination
        if duration < 0.3 and word_count >= 2:
            hallucinations.add(i)
            logger.info(f"  Too short at {sub.start}: {duration:.2f}s for '{sub.content}'")
    
    return hallucinations


def find_matching_subtitle(
    subs: List[srt.Subtitle], 
    start_time: float, 
    end_time: float,
    tolerance: float = 2.0
) -> Tuple[srt.Subtitle, float]:
    """
    Find subtitle that best matches given time range
    
    Returns: (subtitle, overlap_score) or (None, 0)
    """
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
            
            if score > best_score and score > 0.5:  # At least 50% overlap
                best_score = score
                best_match = sub
    
    # If no overlap match, try proximity match
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
    Create hybrid translation:
    - Use WhisperX for normal segments (better context)
    - Use IndICTrans2 for hallucination segments (safer)
    """
    logger.info("=" * 70)
    logger.info("HYBRID SUBTITLE MERGER")
    logger.info("=" * 70)
    logger.info(f"WhisperX:     {whisperx_file}")
    logger.info(f"IndICTrans2:  {indictrans2_file}")
    logger.info(f"Output:       {output_file}")
    logger.info()
    
    # Load subtitles
    logger.info("Loading subtitles...")
    with open(whisperx_file, 'r', encoding='utf-8') as f:
        whisperx_subs = list(srt.parse(f.read()))
    
    with open(indictrans2_file, 'r', encoding='utf-8') as f:
        indictrans2_subs = list(srt.parse(f.read()))
    
    logger.info(f"  WhisperX:     {len(whisperx_subs)} subtitles")
    logger.info(f"  IndICTrans2:  {len(indictrans2_subs)} subtitles")
    logger.info()
    
    # Detect hallucinations
    logger.info("Detecting hallucinations...")
    hallucination_indices = detect_hallucinations(whisperx_subs)
    logger.info(f"  Detected {len(hallucination_indices)} hallucination segments")
    logger.info()
    
    # Build hybrid
    logger.info("Building hybrid translation...")
    hybrid = []
    whisperx_count = 0
    indictrans2_count = 0
    skipped_count = 0
    
    for i, wsub in enumerate(whisperx_subs):
        if i in hallucination_indices:
            # Use IndICTrans2 for this segment
            start_sec = wsub.start.total_seconds()
            end_sec = wsub.end.total_seconds()
            
            match, score = find_matching_subtitle(
                indictrans2_subs,
                start_sec,
                end_sec
            )
            
            if match:
                # Use IndICTrans2 timing and text
                hybrid.append(srt.Subtitle(
                    index=len(hybrid) + 1,
                    start=wsub.start,  # Keep original timing
                    end=wsub.end,
                    content=match.content  # Use IndICTrans2 text
                ))
                indictrans2_count += 1
                
                if verbose:
                    logger.info(f"  {wsub.start} → IndICTrans2: {match.content[:50]}")
            else:
                # No match found, skip this segment
                skipped_count += 1
                if verbose:
                    logger.info(f"  {wsub.start} → SKIPPED (no match)")
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
    logger.info()
    logger.info("Writing hybrid translation...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(srt.compose(hybrid))
    
    # Summary
    logger.info()
    logger.info("=" * 70)
    logger.info("HYBRID TRANSLATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total segments:       {len(hybrid)}")
    logger.info(f"  WhisperX (context): {whisperx_count} ({whisperx_count/len(hybrid)*100:.1f}%)")
    logger.info(f"  IndICTrans2 (safe): {indictrans2_count} ({indictrans2_count/len(hybrid)*100:.1f}%)")
    if skipped_count:
        logger.info(f"  Skipped:            {skipped_count}")
    logger.info()
    logger.info(f"✓ Saved to: {output_file}")
    logger.info()
    logger.info("Benefits:")
    logger.info("  ✓ Context-aware dialogue (WhisperX)")
    logger.info("  ✓ No hallucinations in songs (IndICTrans2)")
    logger.info("  ✓ Best of both worlds!")


def main() -> None:
    """Main."""
    parser = argparse.ArgumentParser(
        description='Merge WhisperX and IndICTrans2 translations into hybrid',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic merge
  python hybrid_subtitle_merger.py \\
    movie.en.whisperx.srt \\
    movie.en.indictrans2.srt \\
    movie.en.hybrid.srt

  # Verbose output
  python hybrid_subtitle_merger.py \\
    movie.en.whisperx.srt \\
    movie.en.indictrans2.srt \\
    movie.en.hybrid.srt \\
    --verbose

  # From job directory
  python hybrid_subtitle_merger.py \\
    out/job/subtitles/movie.en.whisperx.srt \\
    out/job/subtitles/movie.en.indictrans2.srt \\
    out/job/subtitles/movie.en.hybrid.srt
        """
    )
    
    parser.add_argument(
        'whisperx_file',
        type=Path,
        help='WhisperX translation SRT file (context-aware but may have hallucinations)'
    )
    
    parser.add_argument(
        'indictrans2_file',
        type=Path,
        help='IndICTrans2 translation SRT file (safe but less context)'
    )
    
    parser.add_argument(
        'output_file',
        type=Path,
        help='Output hybrid SRT file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output showing each decision'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.whisperx_file.exists():
        logger.error(f"Error: WhisperX file not found: {args.whisperx_file}")
        sys.exit(1)
    
    if not args.indictrans2_file.exists():
        logger.error(f"Error: IndICTrans2 file not found: {args.indictrans2_file}")
        sys.exit(1)
    
    # Create output directory if needed
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge
    merge_translations(
        args.whisperx_file,
        args.indictrans2_file,
        args.output_file,
        args.verbose
    )


if __name__ == '__main__':
    main()
