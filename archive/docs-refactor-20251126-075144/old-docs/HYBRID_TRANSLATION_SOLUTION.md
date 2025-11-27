# Hybrid Translation Solution: WhisperX + IndICTrans2

## The Problem

**WhisperX Direct Translation:**
- ✅ Excellent context awareness (tone, emphasis, natural speech)
- ✅ More natural English for dialogue
- ✅ Better handles conversational nuances
- ❌ Hallucinations in music/songs (repetition loops)

**IndICTrans2 (Text-Based):**
- ✅ No hallucinations
- ✅ Reliable, consistent quality
- ✅ Good for formal content
- ❌ No audio context (misses tone/emphasis)
- ❌ Can be more literal, less natural

## The Solution: Intelligent Hybrid

Combine both methods to get **context-aware translation WITHOUT hallucinations**:

1. Use **WhisperX** for dialogue (better context)
2. Use **IndICTrans2** for songs/music (no hallucinations)
3. Automatically detect and switch between them

---

## Implementation Strategy

### Option 1: Post-Process WhisperX (Quick)

Clean up WhisperX hallucinations after generation:

```python
# scripts/hybrid_subtitle_merger.py

import srt
from pathlib import Path

def detect_hallucinations(subtitles):
    """Detect likely hallucination segments"""
    hallucinations = []
    
    for i in range(len(subtitles) - 2):
        # Check for repetitive text
        if (subtitles[i].content.strip() == 
            subtitles[i+1].content.strip() == 
            subtitles[i+2].content.strip()):
            hallucinations.append(i)
            hallucinations.append(i+1)
            hallucinations.append(i+2)
    
    # Check for excessive segments in short time
    for i in range(len(subtitles)):
        start_time = subtitles[i].start.total_seconds()
        count = sum(1 for s in subtitles[i:i+15] 
                   if s.start.total_seconds() - start_time < 10)
        if count > 12:  # Too many in 10 seconds
            hallucinations.extend(range(i, min(i+15, len(subtitles))))
    
    return set(hallucinations)

def merge_translations(whisperx_srt, indictrans2_srt, output_srt):
    """Merge WhisperX and IndICTrans2, using IndICTrans2 for hallucinations"""
    
    with open(whisperx_srt) as f:
        whisperx_subs = list(srt.parse(f.read()))
    
    with open(indictrans2_srt) as f:
        indictrans2_subs = list(srt.parse(f.read()))
    
    # Detect hallucinations in WhisperX
    hallucination_indices = detect_hallucinations(whisperx_subs)
    
    # Build hybrid
    hybrid = []
    for i, wsub in enumerate(whisperx_subs):
        if i in hallucination_indices:
            # Use IndICTrans2 for this segment
            # Find matching time in IndICTrans2
            isub = find_matching_subtitle(indictrans2_subs, wsub.start, wsub.end)
            if isub:
                hybrid.append(isub)
            # Skip if no match (hallucination only in WhisperX)
        else:
            # Use WhisperX (better context)
            hybrid.append(wsub)
    
    # Write output
    with open(output_srt, 'w') as f:
        f.write(srt.compose(hybrid))
    
    print(f"✓ Created hybrid: {len(hallucination_indices)} segments from IndICTrans2")
    print(f"✓ Used WhisperX for {len(hybrid) - len(hallucination_indices)} segments")

def find_matching_subtitle(subs, start, end):
    """Find subtitle that overlaps with given time range"""
    for sub in subs:
        # Check for time overlap
        if (sub.start <= start <= sub.end or 
            sub.start <= end <= sub.end or
            start <= sub.start <= end):
            return sub
    return None

# Usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python hybrid_subtitle_merger.py whisperx.srt indictrans2.srt output.srt")
        sys.exit(1)
    
    merge_translations(sys.argv[1], sys.argv[2], sys.argv[3])
```

### Option 2: Lyrics-Aware Translation (Better)

Use lyrics detection to intelligently choose translation method:

```python
# scripts/lyrics_aware_translation.py

import json
from pathlib import Path

def create_lyrics_aware_hybrid(job_dir):
    """Create hybrid translation using lyrics detection"""
    
    # Load segments
    segments_file = job_dir / "transcripts" / "segments.json"
    with open(segments_file) as f:
        segments = json.load(f)
    
    # Separate speech and lyrics
    speech_segments = []
    lyrics_segments = []
    
    for seg in segments.get('segments', []):
        # Check if segment is lyrics (you may have this from pipeline)
        if seg.get('is_music', False) or seg.get('is_lyrics', False):
            lyrics_segments.append(seg)
        else:
            speech_segments.append(seg)
    
    print(f"Detected {len(speech_segments)} speech segments")
    print(f"Detected {len(lyrics_segments)} lyrics segments")
    
    # Translate speech with WhisperX (context-aware)
    print("Translating speech with WhisperX (context-aware)...")
    speech_translated = translate_with_whisperx(speech_segments)
    
    # Translate lyrics with IndICTrans2 (no hallucinations)
    print("Translating lyrics with IndICTrans2 (safe)...")
    lyrics_translated = translate_with_indictrans2(lyrics_segments)
    
    # Merge
    all_segments = sorted(
        speech_translated + lyrics_translated,
        key=lambda s: s['start']
    )
    
    # Save
    output_file = job_dir / "transcripts" / "segments_translated_en_hybrid.json"
    with open(output_file, 'w') as f:
        json.dump({'segments': all_segments}, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created hybrid translation: {output_file}")
    return output_file
```

### Option 3: Pipeline Integration (Best)

Add hybrid mode to the pipeline:

```python
# In scripts/run-pipeline.py

def _stage_hybrid_translation(self, target_lang: str) -> bool:
    """
    Hybrid translation stage:
    - Use WhisperX for speech (context-aware)
    - Use IndICTrans2 for lyrics/music (no hallucinations)
    """
    self.logger.info("=" * 80)
    self.logger.info("HYBRID TRANSLATION (WhisperX + IndICTrans2)")
    self.logger.info("=" * 80)
    
    segments_file = self.job_dir / "transcripts" / "segments.json"
    
    # Step 1: Detect lyrics/music segments
    self.logger.info("Detecting lyrics/music segments...")
    from lyrics_detector import detect_lyrics
    
    with open(segments_file) as f:
        segments_data = json.load(f)
    
    segments = segments_data.get('segments', [])
    segments = detect_lyrics(segments)  # Adds 'is_lyrics' flag
    
    speech_segments = [s for s in segments if not s.get('is_lyrics', False)]
    lyrics_segments = [s for s in segments if s.get('is_lyrics', False)]
    
    self.logger.info(f"Speech segments: {len(speech_segments)}")
    self.logger.info(f"Lyrics segments: {len(lyrics_segments)}")
    
    # Step 2: Translate speech with WhisperX (context-aware)
    if speech_segments:
        self.logger.info("Translating speech with WhisperX (context-aware)...")
        speech_translated = self._translate_whisperx(
            speech_segments, 
            target_lang
        )
    else:
        speech_translated = []
    
    # Step 3: Translate lyrics with IndICTrans2 (safe)
    if lyrics_segments:
        self.logger.info("Translating lyrics with IndICTrans2 (no hallucinations)...")
        lyrics_translated = self._translate_indictrans2(
            lyrics_segments,
            target_lang
        )
    else:
        lyrics_translated = []
    
    # Step 4: Merge and sort by time
    all_segments = sorted(
        speech_translated + lyrics_translated,
        key=lambda s: s['start']
    )
    
    # Step 5: Save hybrid translation
    output_file = self.job_dir / "transcripts" / f"segments_translated_{target_lang}_hybrid.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'segments': all_segments}, f, indent=2, ensure_ascii=False)
    
    self.logger.info(f"✓ Hybrid translation complete: {output_file}")
    self.logger.info(f"  - WhisperX (speech): {len(speech_translated)} segments")
    self.logger.info(f"  - IndICTrans2 (lyrics): {len(lyrics_translated)} segments")
    
    return True
```

---

## Quick Solution: Manual Hybrid Creation

For your current job, create the hybrid manually:

```bash
cd /Users/rpatel/Projects/cp-whisperx-app

# Create hybrid translation
python << 'EOF'
import srt
from pathlib import Path

def merge_translations(whisperx_file, indictrans2_file, output_file):
    # Load both
    with open(whisperx_file) as f:
        whisperx_subs = list(srt.parse(f.read()))
    
    with open(indictrans2_file) as f:
        indictrans2_subs = list(srt.parse(f.read()))
    
    # Detect hallucination time range (03:45 - 04:20)
    hallucination_start = 3*60 + 45  # 3:45 in seconds
    hallucination_end = 4*60 + 20     # 4:20 in seconds
    
    hybrid = []
    for i, wsub in enumerate(whisperx_subs):
        start_sec = wsub.start.total_seconds()
        
        # If in hallucination range, use IndICTrans2
        if hallucination_start <= start_sec <= hallucination_end:
            # Find matching IndICTrans2 subtitle
            for isub in indictrans2_subs:
                if abs(isub.start.total_seconds() - start_sec) < 2:  # Within 2 seconds
                    hybrid.append(srt.Subtitle(
                        index=len(hybrid) + 1,
                        start=wsub.start,
                        end=wsub.end,
                        content=isub.content  # Use IndICTrans2 text
                    ))
                    break
        else:
            # Use WhisperX (better context)
            hybrid.append(srt.Subtitle(
                index=len(hybrid) + 1,
                start=wsub.start,
                end=wsub.end,
                content=wsub.content
            ))
    
    # Write
    with open(output_file, 'w') as f:
        f.write(srt.compose(hybrid))
    
    print(f"✓ Created hybrid: {output_file}")
    print(f"  Total segments: {len(hybrid)}")

# Run
merge_translations(
    "out/2025/11/23/rpatel/4/subtitles/Jaane Tu Ya Jaane Na.en.whisperx.srt",
    "out/2025/11/23/rpatel/4/subtitles/Jaane Tu Ya Jaane Na.en.indictrans2.srt",
    "out/2025/11/23/rpatel/4/subtitles/Jaane Tu Ya Jaane Na.en.hybrid.srt"
)
EOF
```

---

## Configuration for Future Jobs

Add hybrid mode to job.json:

```json
{
  "workflow": "subtitle",
  "source_language": "hi",
  "target_languages": ["en"],
  
  "translation": {
    "method": "hybrid",
    "hybrid_config": {
      "speech_translator": "whisperx",
      "lyrics_translator": "indictrans2",
      "auto_detect_lyrics": true
    }
  },
  
  "source_separation": {
    "enabled": true,
    "quality": "quality"
  }
}
```

---

## Comparison: All Methods

| Segment Type | WhisperX Direct | IndICTrans2 | **Hybrid** |
|--------------|-----------------|-------------|------------|
| **Dialogue** | ⭐⭐⭐⭐⭐ Natural | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Natural |
| **Songs** | ❌ Hallucinations | ⭐⭐⭐⭐ Clean | ⭐⭐⭐⭐ Clean |
| **Hinglish** | ⭐⭐⭐⭐ Context | ⭐⭐⭐⭐ Accurate | ⭐⭐⭐⭐⭐ Best |
| **Emphasis** | ⭐⭐⭐⭐⭐ Captures | ⭐⭐ Misses | ⭐⭐⭐⭐⭐ Captures |
| **Production** | ❌ Not safe | ✅ Safe | ✅ Safe |

**Hybrid = Best of both worlds!**

---

## Benefits of Hybrid Approach

### 1. **Context-Aware Dialogue**
```
WhisperX: "Listen, the flight is late anyway."
(Captures casual tone, natural speech)

IndICTrans2: "Listen, the flight is late anyway."
(Similar but may miss subtle emphasis)

Hybrid: Uses WhisperX for this (better)
```

### 2. **Safe Lyrics Translation**
```
WhisperX: "Okay. Okay. Okay..." (hallucination)

IndICTrans2: "If you're bored, I'll explain, okay?"
(Clean, accurate)

Hybrid: Uses IndICTrans2 for this (safer)
```

### 3. **Intelligent Detection**
- Automatically identifies problem segments
- Switches translation method dynamically
- Best quality for each segment type

---

## Implementation Priority

### Phase 1: Quick Win (Manual)
```bash
# Create hybrid for current job
python scripts/hybrid_subtitle_merger.py \
  whisperx.srt indictrans2.srt hybrid.srt
```

### Phase 2: Automated Script
```bash
# Add to toolkit
python scripts/create_hybrid_translation.py \
  --job-dir out/2025/11/23/rpatel/4 \
  --method auto  # Auto-detect hallucinations
```

### Phase 3: Pipeline Integration
```bash
# Add hybrid mode to prepare-job
./prepare-job.sh -i movie.mp4 -l hi -t en \
  --translation-method hybrid
```

---

## Recommendation

**For your Bollywood content:**

1. **Primary**: Use hybrid approach
   - WhisperX for dialogue (⭐⭐⭐⭐⭐ context)
   - IndICTrans2 for songs (⭐⭐⭐⭐ safe)

2. **Fallback**: Use IndICTrans2 only
   - Safe, consistent
   - Good quality
   - No hallucinations

3. **Research**: Use WhisperX direct
   - Best natural language
   - Manual review required
   - Not production-safe

**Best workflow:**
```bash
# Generate both
./run-pipeline.sh out/[job]  # Gets IndICTrans2

python scripts/whisperx_translate_comparator.py out/[job]  # Gets WhisperX

# Create hybrid (manual or automated)
python scripts/create_hybrid.py out/[job]  # Best of both!
```

---

## Next Steps

1. **Try Manual Hybrid**: Run the quick Python script above to create hybrid for your current job

2. **Test Quality**: Compare dialogue segments (WhisperX better?) vs song segments (IndICTrans2 safer?)

3. **Automate**: If results are good, I can create full automated hybrid script

4. **Pipeline Integration**: Add as optional translation method in pipeline

---

**Would you like me to create the automated hybrid merger script right now?**

This would:
- Automatically detect hallucination segments
- Merge WhisperX + IndICTrans2 intelligently  
- Give you context-aware dialogue + safe lyrics
- Best of both worlds!
