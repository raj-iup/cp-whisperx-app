#!/usr/bin/env python3
"""
Compare NLLB vs IndicTrans2 translations
Shows side-by-side comparison of English subtitles
"""
import sys
from pathlib import Path

def load_srt(srt_file):
    """Load SRT file and parse subtitles"""
    import srt
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return list(srt.parse(content))

def compare_translations(job_dir):
    """Compare NLLB and IndicTrans2 translations"""
    subtitles_dir = Path(job_dir) / "subtitles"
    
    # Find subtitle files
    nllb_srt = list(subtitles_dir.glob("*.en.srt"))[0]
    indictrans_srt = list(subtitles_dir.glob("*.en.indictrans2.srt"))[0]
    hindi_srt = list(subtitles_dir.glob("*.hi.srt"))[0]
    
    print("=" * 100)
    print("TRANSLATION COMPARISON: NLLB vs IndicTrans2")
    print("=" * 100)
    print()
    print(f"Original (Hindi):     {hindi_srt.name}")
    print(f"NLLB Translation:     {nllb_srt.name}")
    print(f"IndicTrans2 Translation: {indictrans_srt.name}")
    print()
    print("=" * 100)
    print()
    
    # Load subtitles
    nllb_subs = load_srt(nllb_srt)
    indictrans_subs = load_srt(indictrans_srt)
    hindi_subs = load_srt(hindi_srt)
    
    # Show sample comparisons
    print("SAMPLE COMPARISONS (First 15 subtitles):")
    print("=" * 100)
    print()
    
    for i in range(min(15, len(nllb_subs))):
        print(f"[{i+1}] Time: {nllb_subs[i].start} --> {nllb_subs[i].end}")
        print()
        print(f"  Hindi:        {hindi_subs[i].content}")
        print()
        print(f"  NLLB:         {nllb_subs[i].content}")
        print()
        print(f"  IndicTrans2:  {indictrans_subs[i].content}")
        print()
        print("-" * 100)
        print()
    
    # Statistics
    print()
    print("=" * 100)
    print("STATISTICS")
    print("=" * 100)
    print()
    print(f"Total subtitles: {len(nllb_subs)}")
    print()
    
    # Count differences
    different = 0
    for i in range(len(nllb_subs)):
        if nllb_subs[i].content != indictrans_subs[i].content:
            different += 1
    
    print(f"Identical translations: {len(nllb_subs) - different}/{len(nllb_subs)}")
    print(f"Different translations: {different}/{len(nllb_subs)} ({different/len(nllb_subs)*100:.1f}%)")
    print()
    
    # Average lengths
    nllb_avg = sum(len(s.content) for s in nllb_subs) / len(nllb_subs)
    indictrans_avg = sum(len(s.content) for s in indictrans_subs) / len(indictrans_subs)
    
    print(f"Average length (NLLB):        {nllb_avg:.1f} characters")
    print(f"Average length (IndicTrans2): {indictrans_avg:.1f} characters")
    print()
    
    print("=" * 100)
    print()
    print("Files available for review:")
    print(f"  {nllb_srt}")
    print(f"  {indictrans_srt}")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_dir = sys.argv[1]
    else:
        job_dir = "out/2025/11/23/rpatel/4"
    
    compare_translations(job_dir)
