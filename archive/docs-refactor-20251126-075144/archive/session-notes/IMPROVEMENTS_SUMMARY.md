# Audio Quality Improvements - Complete Guide

## What We've Done ✅

### 1. Anti-Hallucination Fix (Completed)
**Problem:** Repeated "प्रश्न प्रश्न" in transcript  
**Solution:** Disabled `condition_on_previous_text` + added filtering parameters  
**Files:** `scripts/whisper_backends.py`, `scripts/whisperx_integration.py`  
**Status:** ✅ LIVE - Active in all transcriptions

---

## What You Can Do Now 🚀

### Your Specific Challenge
**Content:** Credits (0:00-4:01) + Song + Dialogue with Background Music  
**Issue:** Music/vocalizations interfere with dialogue transcription

### Solutions Ranked by Impact

#### 🥇 Option 1: Scene Selection (Easiest, Immediate)
**Effort:** 0 minutes  
**Impact:** High

```bash
# Skip credits, use dialogue portion only
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:04:01" --end "00:07:00" \
                 --source-lang hi --target-langs en,gu

# Or pick a pure dialogue scene (best)
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:15:00" --end "00:18:00" \
                 --source-lang hi --target-langs en,gu
```

**When to use:** Always start here

---

#### 🥈 Option 2: Source Separation (Best Quality)
**Effort:** 2 minutes per clip  
**Impact:** Very High  

Remove background music completely using AI:

```bash
# 1. Install
pip install demucs

# 2. Extract clip
ffmpeg -i "in/Jaane Tu Ya Jaane Na 2008.mp4" \
       -ss 00:01:30 -to 00:05:30 \
       -vn -ar 44100 -ac 2 clip.wav

# 3. Separate vocals from music
demucs --two-stems=vocals clip.wav -o separated/

# 4. Use separated vocals for transcription
# Result: separated/htdemucs/clip/vocals.wav (music-free)
```

**When to use:**
- Credits with dialogue
- Songs with dialogue
- Heavy background music
- Bollywood movies (music-heavy)

**See:** `SOURCE_SEPARATION_GUIDE.md` for details

---

#### 🥉 Option 3: Enhanced VAD Preprocessing
**Effort:** Medium  
**Impact:** Medium-High

Use stricter speech detection to filter out music:

```bash
# Run PyAnnote VAD with music-optimized settings
python scripts/pyannote_vad_chunker.py audio.wav \
    --device mps \
    --merge-gap 0.3 \
    --out-json speech_only.json

# This identifies ONLY dialogue regions
# Then transcribe only those regions
```

**When to use:** Moderate background music

---

## Quick Decision Guide

### For Your Current Clip (1:30-5:30 with credits + song)

**Fastest:**
```bash
# Option A: Skip to dialogue (4:01+)
./prepare-job.sh --start "00:04:01" --end "00:07:00" ...
```

**Best Quality:**
```bash
# Option B: Source separation
ffmpeg -i movie.mp4 -ss 00:01:30 -to 00:05:30 clip.wav
demucs --two-stems=vocals clip.wav
# Use separated vocals
```

**Balanced:**
```bash
# Option C: Pick different scene entirely
./prepare-job.sh --start "00:15:00" --end "00:18:00" ...
```

---

## What's Already Working

### ✅ Active Now
1. **Anti-hallucination parameters** - Prevents repetition loops
2. **Built-in VAD** - Silero VAD in WhisperX
3. **Word-level alignment** - Accurate timestamps
4. **Multi-language support** - Hindi, Gujarati, English

### 📊 Results You Can Expect
With anti-hallucination fix:
- ✅ No more repeated phrases
- ✅ Better handling of silence/music
- ✅ More accurate word timestamps
- ✅ Filtered low-confidence outputs

With source separation:
- ✅ Music completely removed
- ✅ Clean dialogue only
- ✅ No song vocalizations
- ✅ Professional-quality transcription

---

## Next Steps

### Immediate (Today)
1. **Try better scene selection** - Dialogue-heavy clip
2. **Test anti-hallucination fix** - Re-run with current improvements
3. **Optional:** Test source separation on problem clip

### This Week
1. Install Demucs for source separation
2. Test on multiple clips
3. Document which scenes work best

### Future
1. Automate source separation in pipeline
2. Add scene classification
3. Implement adaptive processing

---

## All Documentation

1. **HALLUCINATION_FIX_SUMMARY.md** - Quick anti-hallucination reference
2. **ANTI_HALLUCINATION_FIX.md** - Complete technical details
3. **SOURCE_SEPARATION_GUIDE.md** - Music removal guide
4. **ADVANCED_AUDIO_IMPROVEMENTS.md** - All available improvements
5. **SCENE_SELECTION_TIPS.md** - How to pick good scenes
6. **This file** - Quick reference summary

---

## Quick Commands

### Test Current Anti-Hallucination Fix
```bash
# Just re-run with better scene selection
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:15:00" --end "00:18:00" \
                 --source-lang hi --target-langs en,gu
./run-pipeline.sh
```

### Test Source Separation
```bash
# Install and test on your clip
pip install demucs
ffmpeg -i "in/Jaane Tu Ya Jaane Na 2008.mp4" \
       -ss 00:01:30 -to 00:05:30 -vn test.wav
demucs --two-stems=vocals test.wav
afplay separated/htdemucs/test/vocals.wav  # Listen
```

### Check Results
```bash
# View transcript diversity
jq -r '.segments[].text' out/*/transcripts/segments.json | head -10

# Check parameters in log
grep "condition_on_previous_text\|hallucination" out/*/logs/*.log
```

---

## Summary

**You Asked:** *"What else can we do to improve credits + songs + background music?"*

**Answer:**

### ✅ Already Fixed
- Anti-hallucination parameters active

### 🎯 Recommended Next
1. **Scene selection** (0 effort, high impact)
2. **Source separation** (2 min effort, very high impact)
3. **Enhanced VAD** (medium effort, medium impact)

### 🏆 Best Combination
```
Better Scene Selection + Anti-Hallucination + Source Separation
= Professional-quality transcription
```

**My Recommendation:** Start with scene selection (4:01+ or different scene). If you still need better quality for music-heavy content, add source separation. The anti-hallucination fix handles the rest automatically.

---

**Want to implement any of these? Let me know:**
- A) Automate source separation in pipeline
- B) Add enhanced VAD preprocessing  
- C) Implement scene classification
- D) All of the above
