# WhisperX Translation Hallucinations - Known Issue

## Issue Description

WhisperX's direct translation feature (task='translate') can produce hallucinations, particularly during:
- **Music/song segments**
- **Background noise**
- **Low speech content**
- **Repetitive phrases**

### Example Hallucination

**Time**: 03:45-04:00 (during song segment)  
**Expected**: "I'll tell you when I'm bored, okay?"  
**WhisperX Output**: Repeats "Okay" 20+ times in rapid succession

```srt
105
00:03:52,010 --> 00:03:52,270
Okay.

106
00:03:52,570 --> 00:03:53,231
Okay.

107
00:03:53,251 --> 00:03:54,552
Okay.

[... repeats 15+ more times ...]
```

---

## Root Cause

WhisperX's translation task:
1. **No conditioning on previous text** - Each segment independent
2. **Music interference** - Songs confuse the model
3. **Token repetition loop** - Gets stuck on common words
4. **No post-processing** - Direct model output without filtering

---

## Why Post-Transcription Translation is Better

The main pipeline avoids this by:

### Method 1: Transcribe First, Then Translate

```
Audio → WhisperX (transcribe only) → IndICTrans2/NLLB (translate text)
```

**Advantages:**
1. ✅ **Lyrics detection** - Identifies and handles song segments
2. ✅ **Anti-hallucination** - Prevents repetition loops
3. ✅ **condition_on_previous_text=False** - Breaks hallucination chains
4. ✅ **Text-based translation** - More stable, less prone to audio artifacts

### Method 2: Use Pipeline Features

The main pipeline includes:

**Anti-Hallucination System:**
- `condition_on_previous_text: false` - Prevents context loops
- Temperature fallback - Multiple attempts with different settings
- Compression ratio threshold - Detects repetitive output
- Logprob filtering - Removes low-confidence segments

**Lyrics Detection:**
- Identifies song segments
- Special handling for musical content
- Reduces hallucinations in music

**Source Separation:**
- Removes background music
- Isolates vocals
- Cleaner audio for transcription

---

## Solutions

### Solution 1: Use Main Pipeline (Recommended)

Instead of direct WhisperX translation, use the full pipeline:

```bash
# This avoids hallucinations
./prepare-job.sh -i movie.mp4 -l hi -t en -w subtitle
./run-pipeline.sh out/[job-id]

# Outputs:
# - movie.en.srt (NLLB - from text)
# - movie.en.indictrans2.srt (IndICTrans2 - from text)
```

**Why it works:**
- WhisperX only transcribes (task='transcribe')
- Text translation by IndICTrans2/NLLB
- Anti-hallucination features active
- Lyrics detection enabled
- Source separation removes music

### Solution 2: Post-Process WhisperX Output

If you already have WhisperX translation:

```python
# scripts/remove_hallucinations.py (create this)
import srt
from pathlib import Path

def remove_repetitions(subtitles, max_repeat=3):
    """Remove subtitle entries with excessive repetition"""
    cleaned = []
    prev_text = None
    repeat_count = 0
    
    for sub in subtitles:
        text = sub.content.strip().lower()
        
        if text == prev_text:
            repeat_count += 1
            if repeat_count >= max_repeat:
                continue  # Skip this repetitive entry
        else:
            repeat_count = 0
            prev_text = text
        
        cleaned.append(sub)
    
    return cleaned

# Usage
with open('movie.en.whisperx.srt', 'r') as f:
    subs = list(srt.parse(f.read()))

cleaned = remove_repetitions(subs, max_repeat=3)

with open('movie.en.whisperx.cleaned.srt', 'w') as f:
    f.write(srt.compose(cleaned))
```

### Solution 3: Hybrid Approach

Use WhisperX for most content, but switch to text-based translation for problematic segments:

```bash
# 1. Identify song segments
python scripts/lyrics_detection.py out/[job]/transcripts/segments.json

# 2. Split subtitles into speech/song
python scripts/split_by_lyrics.py movie.en.whisperx.srt

# 3. Retranslate song segments from Hindi text
python scripts/retranslate_srt.py \
  movie.hi.srt \
  -o movie.en.lyrics_fixed.srt \
  --method indictrans2 \
  --segments-only [song_segments]

# 4. Merge back together
python scripts/merge_subtitles.py \
  movie.en.whisperx.srt \
  movie.en.lyrics_fixed.srt \
  -o movie.en.final.srt
```

### Solution 4: Manual Cleanup

For small number of hallucinations:

```bash
# Find repetitive segments
grep -n "^Okay\.$" movie.en.whisperx.srt

# Edit manually or use sed
sed -i '/^Okay\.$/d' movie.en.whisperx.srt  # Remove all "Okay."
```

---

## Comparison: Translation Methods

### WhisperX Direct Translation (task='translate')

**Pros:**
- ✅ Single pass (faster)
- ✅ Audio context (prosody, tone)
- ✅ Good for clean speech

**Cons:**
- ❌ Hallucinations in music
- ❌ Repetition loops
- ❌ No anti-hallucination features
- ❌ Harder to post-process

**Use when:**
- Clean dialogue only
- No music/songs
- Short clips
- You can manually review

### Post-Transcription Translation (Pipeline)

**Pros:**
- ✅ Anti-hallucination features
- ✅ Lyrics detection
- ✅ Source separation option
- ✅ Multiple translation methods
- ✅ Stable, production-ready

**Cons:**
- ❌ Two-pass (slower)
- ❌ No audio context in translation
- ❌ May miss tone/emphasis

**Use when:**
- Content has music/songs (Bollywood!)
- Production quality needed
- Batch processing
- Want multiple translation options

---

## Prevention Strategies

### For Future Jobs

**1. Enable Source Separation:**
```json
{
  "source_separation": {
    "enabled": true,
    "quality": "quality"
  }
}
```

Removes background music before transcription.

**2. Use Two-Step Workflow:**
```bash
# Step 1: Transcribe only
./prepare-job.sh -i movie.mp4 -l hi -w transcribe

# Step 2: Translate from text
./prepare-job.sh -i movie.mp4 -l hi -t en -w translate
```

**3. Enable Lyrics Detection:**
Automatic in pipeline, marks song segments.

**4. Use Anti-Hallucination Settings:**
Already enabled in main pipeline:
```python
condition_on_previous_text=False
compression_ratio_threshold=2.4
logprob_threshold=-1.0
```

---

## When to Use WhisperX Translation

### ✅ Good Use Cases

- **Clean dialogue**: Interviews, podcasts, narration
- **Short clips**: <5 minutes, easy to review
- **No music**: Pure speech content
- **Context matters**: Tone/emphasis changes meaning
- **Hinglish**: Audio cues help language boundaries

### ❌ Avoid For

- **Bollywood movies**: Too much music
- **Long content**: >30 minutes
- **Production use**: Without manual review
- **Batch processing**: Too many hallucinations to fix
- **Songs/music**: Always use text-based translation

---

## Hallucination Detection

### Automatic Detection

```python
def detect_hallucinations(srt_file):
    """Detect likely hallucinations"""
    with open(srt_file, 'r') as f:
        subs = list(srt.parse(f.read()))
    
    issues = []
    
    # Check for repetitions
    for i in range(len(subs) - 2):
        if (subs[i].content == subs[i+1].content == subs[i+2].content):
            issues.append(f"Repetition at {subs[i].start}: {subs[i].content}")
    
    # Check for very short segments
    for sub in subs:
        duration = (sub.end - sub.start).total_seconds()
        if duration < 0.3 and len(sub.content) > 2:
            issues.append(f"Too short at {sub.start}: {duration}s")
    
    # Check for excessive segments in short time
    time_window = 10  # seconds
    for i in range(len(subs)):
        start_time = subs[i].start.total_seconds()
        segments_in_window = sum(
            1 for s in subs[i:i+20]
            if s.start.total_seconds() - start_time < time_window
        )
        if segments_in_window > 15:
            issues.append(f"Excessive segments at {subs[i].start}: {segments_in_window} in {time_window}s")
    
    return issues
```

---

## Recommendations

### For Your Current File

**Jaane Tu Ya Jaane Na.en.whisperx.srt:**

1. **Use text-based translation for song segments**:
   - The "Okay" repetitions are during a song
   - Use IndICTrans2 or NLLB translation instead
   - Already available: `Jaane Tu Ya Jaane Na.en.indictrans2.srt`

2. **Compare translations**:
   ```bash
   # IndICTrans2 likely better for this content
   diff out/.../Jaane\ Tu\ Ya\ Jaane\ Na.en.whisperx.srt \
        out/.../Jaane\ Tu\ Ya\ Jaane\ Na.en.indictrans2.srt
   ```

3. **Hybrid approach**:
   - Use WhisperX for dialogue (it's good!)
   - Use IndICTrans2 for songs (no hallucinations)
   - Manually merge or create script to automate

### General Recommendation

**For Bollywood content:**
```bash
# Best workflow:
1. Enable source separation
2. Use transcribe workflow (not translate)
3. Use IndICTrans2 for Hinglish Hindi→English
4. Compare with NLLB if needed
5. Use WhisperX translation only for comparison/research
```

**WhisperX translation best for:**
- Hollywood/English content translated to other languages
- Clean dialogue scenes
- Research/comparison purposes
- When audio context critical

---

## Documentation

- [Anti-Hallucination Guide](./user-guide/features/anti-hallucination.md)
- [Lyrics Detection](./user-guide/features/lyrics-detection.md)
- [Source Separation](./user-guide/features/source-separation.md)
- [Translation Comparison](./WHISPERX_TRANSLATION_COMPARISON.md)

---

## Summary

✅ **WhisperX translation works** but has limitations  
⚠️ **Hallucinations occur** especially in music  
✅ **Main pipeline avoids this** with multi-step approach  
📊 **Best practice**: Use for comparison, not primary translation  
🎵 **Bollywood**: Always use text-based translation for songs

**Your case**: The hallucinations are during a song segment. Use the IndICTrans2 translation instead for this content - it's already generated and doesn't have hallucinations.

---

**Last Updated**: November 24, 2025  
**Status**: Known limitation, documented solutions available
