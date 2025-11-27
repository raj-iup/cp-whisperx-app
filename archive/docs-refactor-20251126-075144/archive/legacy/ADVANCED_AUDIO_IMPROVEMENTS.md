# Advanced Audio Improvements for Challenging Content
## Handling Credits, Songs, and Background Music

**Date:** 2025-11-21  
**Context:** Your "Jaane Tu Ya Jaane Na" clip (1:30-5:30) contains:
- Opening credits (up to 4:01)
- Song with vocalizations ("aa...aa...")
- Dialogue with background music

---

## Current Status ✅

### Already Implemented
1. **Anti-Hallucination Parameters** (just added)
   - `condition_on_previous_text=False`
   - `logprob_threshold=-1.0`
   - `no_speech_threshold=0.6`
   - `compression_ratio_threshold=2.4`

### Currently Active
2. **WhisperX Built-in VAD**
   - Silero VAD runs automatically during transcription
   - Default thresholds (not optimized for music-heavy content)

---

## Additional Improvements Available

### 🎯 Priority 1: Audio Preprocessing (Highest Impact)

#### 1.1 Source Separation (Remove Background Music)
Extract clean vocals before transcription using AI-powered source separation.

**Tools Available:**
- **Demucs** (Meta/Facebook) - State-of-the-art source separation
- **Spleeter** (Deezer) - Faster, good quality

**Implementation:**

```bash
# Install Demucs
pip install demucs

# Separate vocals from music
demucs --two-stems=vocals "input_audio.wav" -o separated/

# This creates: separated/htdemucs/input_audio/vocals.wav
```

**Integration Point:**
Add as preprocessing stage before ASR:
```
Pipeline: Demux → [NEW: Source Separation] → VAD → ASR → ...
```

**Benefits:**
- ✅ Removes background music completely
- ✅ Cleaner audio = better transcription
- ✅ Works great for Bollywood movies (music-heavy)
- ✅ Preserves dialogue quality

**Drawbacks:**
- ⏱️ Adds processing time (~1-2 minutes per 5-minute clip)
- 💾 Requires extra disk space for separated tracks

---

#### 1.2 Enhanced VAD (PyAnnote)
Use dedicated VAD preprocessing to identify speech-only regions before ASR.

**Current Situation:**
- WhisperX uses Silero VAD (built-in, default settings)
- PyAnnote VAD scripts exist but **NOT used** in pipeline

**PyAnnote VAD Advantages:**
- 🎯 Better at distinguishing speech from music
- 🎯 More accurate segment boundaries
- 🎯 Configurable thresholds
- 🎯 Handles overlapping speakers better

**Implementation:**

```bash
# Already installed, just need to activate in pipeline
# Modify pipeline to run VAD stage explicitly:

# In run-pipeline.sh, add VAD stage:
pyannote_vad → outputs speech_segments.json
↓
Pass to WhisperX: only transcribe detected speech regions
```

**Configuration Options:**
```python
# In scripts/pyannote_vad_chunker.py
# Can tune these parameters:

onset = 0.5       # Speech start threshold (0-1)
                  # Higher = more conservative (fewer false positives)
                  # Lower = catch more speech (may include music)

offset = 0.5      # Speech end threshold (0-1)
                  # Higher = longer segments
                  # Lower = shorter, cleaner segments

min_duration_on = 0.0   # Minimum speech duration (seconds)
                        # Increase to filter very short sounds

min_duration_off = 0.0  # Minimum silence duration (seconds)
                        # Increase to merge close segments
```

**For Music-Heavy Content:**
```python
# Recommended settings for credits + songs + dialogue
onset = 0.7           # More conservative (avoid music)
offset = 0.3          # Quicker to end (don't extend into music)
min_duration_on = 0.5 # Filter short vocalizations
min_duration_off = 0.3 # Merge close dialogue
```

---

### 🎯 Priority 2: Whisper Model Tuning

#### 2.1 Prompt Engineering
Guide the model with context about the content type.

**Already Implemented:**
- `initial_prompt` support in backends
- Bias window system for character names

**New Enhancement:**
Add content-type prompts:

```python
# For dialogue-heavy scenes
initial_prompt = "This is a Hindi dialogue scene from a Bollywood movie."

# For mixed content (credits + dialogue)
initial_prompt = "Hindi movie dialogue. Ignore background music and credits."

# For specific movies
initial_prompt = "Jaane Tu Ya Jaane Na dialogue between Jai and Aditi."
```

**Implementation:**
```bash
# Add to job configuration
./prepare-job.sh --media "movie.mp4" \
                 --initial-prompt "Hindi dialogue, ignore music" \
                 --source-lang hi
```

---

#### 2.2 Temperature Adjustment
Control transcription randomness/creativity.

**Current:** Default temperature fallback cascade
```python
temperature = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
```

**For Challenging Audio:**
```python
# Use lower temperatures only (more deterministic)
temperature = [0.0, 0.2]  # More conservative, less hallucination
```

**Implementation:**
Already supported in `WhisperXProcessor`:
```python
processor = WhisperXProcessor(
    temperature="0.0,0.2",  # Comma-separated
    # ... other params
)
```

---

#### 2.3 Language-Specific Models
Some Whisper models are better for specific languages.

**Current:** `large-v3` (multilingual)

**Alternatives:**
- `large-v3` - Best overall, but slower
- `medium` - 2x faster, still very accurate for Hindi
- `small` - 4x faster, good for testing

**For Hindi specifically:**
```bash
# Test with medium model (faster, still accurate)
# Modify job config or pass to processor:
model_name = "medium"
```

---

### 🎯 Priority 3: Post-Processing Filters

#### 3.1 Music Detection Filter
Automatically detect and remove music-only segments.

**Implementation Approach:**
```python
def filter_music_segments(segments, audio_file):
    """
    Remove segments that are likely music/songs
    Based on:
    - Low confidence scores
    - Repetitive patterns
    - Specific keywords ("aa", "la", "hmm")
    """
    filtered = []
    for seg in segments:
        text = seg['text'].strip().lower()
        
        # Filter repetitive vocalizations
        if is_repetitive_vocalization(text):
            continue
            
        # Filter based on confidence
        if seg.get('confidence', 1.0) < 0.3:
            continue
            
        # Filter musical patterns
        if is_musical_pattern(text):
            continue
            
        filtered.append(seg)
    
    return filtered

def is_repetitive_vocalization(text):
    # Detect "aa aa aa", "la la la", etc.
    words = text.split()
    if len(words) < 3:
        return False
    
    # Check if all words are similar
    unique_words = set(words)
    if len(unique_words) <= 2 and len(words) >= 3:
        return True
    
    return False
```

---

#### 3.2 Confidence-Based Filtering
Already partially supported, enhance it:

```python
# Enhanced filtering in post-processing
MIN_CONFIDENCE = 0.4  # Adjust based on needs

segments_filtered = [
    seg for seg in segments
    if seg.get('avg_logprob', 0) > logprob_threshold
    and seg.get('no_speech_prob', 1.0) < no_speech_threshold
    and segment_has_valid_speech(seg)
]
```

---

### 🎯 Priority 4: Workflow Optimization

#### 4.1 Two-Pass Transcription
1st pass: Identify speech regions  
2nd pass: Transcribe only clean dialogue

```bash
# Pass 1: Aggressive VAD to find all potential speech
pyannote_vad --onset 0.3 --offset 0.5 audio.wav

# Pass 2: Transcribe only high-confidence speech regions
whisperx transcribe --vad-segments speech_segments.json
```

---

#### 4.2 Scene-Aware Processing
Process different types of content with different settings.

**Scene Classification:**
```python
def classify_scene(audio_segment):
    """
    Classify audio segment type:
    - dialogue (conversation between speakers)
    - song (music with lyrics)
    - credits (background music + text overlay)
    - action (sound effects, minimal dialogue)
    """
    # Use audio features:
    # - Energy levels
    # - Zero-crossing rate
    # - Spectral features
    # - VAD segment density
```

**Adaptive Processing:**
```python
if scene_type == "dialogue":
    # Standard settings
    onset = 0.5
    no_speech_threshold = 0.6
    
elif scene_type == "song":
    # Skip or use special lyrics mode
    skip = True
    
elif scene_type == "credits":
    # Very aggressive filtering
    onset = 0.8
    no_speech_threshold = 0.8
```

---

## Recommended Implementation Priority

### Phase 1: Quick Wins (Immediate)
1. ✅ **Anti-hallucination parameters** (DONE)
2. **Scene selection** - Use dialogue-heavy clips for testing
3. **Initial prompts** - Add content hints

### Phase 2: Moderate Effort (1-2 days)
1. **Enhanced VAD preprocessing** - Activate PyAnnote VAD stage
2. **VAD parameter tuning** - Optimize for music-heavy content
3. **Post-processing filters** - Remove music/vocalization segments

### Phase 3: Advanced (3-5 days)
1. **Source separation** - Demucs integration
2. **Two-pass transcription** - VAD + targeted ASR
3. **Scene classification** - Adaptive processing

---

## Quick Test: Enhanced VAD

Let me show you how to enable enhanced VAD right now:

### Step 1: Enable PyAnnote VAD Stage
```bash
# Edit run-pipeline.sh to add VAD stage before ASR
# Or manually run:

# 1. Extract audio
ffmpeg -i "in/movie.mp4" -vn -ar 16000 -ac 1 audio.wav

# 2. Run PyAnnote VAD with tuned parameters
python scripts/pyannote_vad_chunker.py audio.wav \
    --device mps \
    --merge-gap 0.3 \
    --out-json speech_segments.json

# 3. Pass segments to ASR (manual for now)
# Later: integrate into pipeline
```

### Step 2: Add Source Separation (Optional)
```bash
# Install Demucs
pip install demucs

# Separate vocals
demucs --two-stems=vocals audio.wav -o separated/

# Use separated vocals for transcription
# This removes ALL background music
```

---

## Configuration Template

For your specific use case (Bollywood movies with music):

```python
# Recommended settings for music-heavy content

# 1. Anti-Hallucination (DONE)
condition_on_previous_text = False
logprob_threshold = -1.0
no_speech_threshold = 0.6
compression_ratio_threshold = 2.4

# 2. VAD Settings (TO ADD)
vad_onset = 0.7              # More conservative
vad_offset = 0.3             # Quicker to end
min_speech_duration = 0.5    # Filter short sounds
merge_gap = 0.3              # Merge close dialogue

# 3. Whisper Settings (AVAILABLE)
temperature = [0.0, 0.2]     # More deterministic
initial_prompt = "Hindi movie dialogue, ignore background music"

# 4. Post-Processing (TO ADD)
filter_repetitive_vocalizations = True
filter_low_confidence = True
min_confidence = 0.4
```

---

## Specific Recommendations for Your Clip

Your "Jaane Tu Ya Jaane Na" (1:30-5:30) clip:

### Option A: Source Separation (Best Quality)
```bash
# 1. Install Demucs
pip install demucs

# 2. Extract and separate
ffmpeg -i "in/Jaane Tu Ya Jaane Na 2008.mp4" \
       -ss 00:01:30 -to 00:05:30 \
       -vn -ar 16000 -ac 1 test_audio.wav

demucs --two-stems=vocals test_audio.wav -o separated/

# 3. Transcribe clean vocals
# (integrate this into pipeline later)
```

### Option B: Enhanced VAD (Quick)
```bash
# Use PyAnnote VAD with strict settings
# Add to pipeline or run manually:

python scripts/pyannote_vad_chunker.py test_audio.wav \
    --device mps \
    --merge-gap 0.3 \
    --out-json speech_only.json

# This will identify ONLY the dialogue portions (after 4:01)
```

### Option C: Smart Scene Selection (Easiest)
```bash
# Skip the problematic credits section entirely
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:04:01" --end "00:07:00" \
                 --source-lang hi --target-langs en,gu

# Or pick a pure dialogue scene
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:15:00" --end "00:18:00" \
                 --source-lang hi --target-langs en,gu
```

---

## Next Steps

### Immediate (Today)
1. ✅ Anti-hallucination fix is live
2. Test with dialogue portion only (4:01-7:00)
3. Or pick a clearer scene (15:00-18:00)

### Short-term (This Week)
1. Add initial_prompt support to prepare-job
2. Integrate PyAnnote VAD as optional preprocessing stage
3. Test Demucs source separation on sample clip

### Medium-term (Next Sprint)
1. Implement post-processing filters
2. Add scene classification
3. Create adaptive processing modes

---

## Summary

**The anti-hallucination fix will help**, but for **credits + songs + music**, you have multiple options:

| Approach | Effort | Impact | When to Use |
|----------|--------|--------|-------------|
| **Scene Selection** | Low | High | Best first step |
| **Anti-Hallucination** | Done ✅ | Medium | Always use |
| **Enhanced VAD** | Medium | High | Music-heavy scenes |
| **Source Separation** | Medium | Very High | Maximum quality |
| **Post-Processing** | High | Medium | Fine-tuning |
| **Two-Pass** | High | High | Production use |

**My Recommendation:**
1. Start with **better scene selection** (dialogue-heavy)
2. The **anti-hallucination fix handles the rest**
3. If still needed, add **source separation** for music-heavy content

---

**Want me to implement any of these?** Let me know which option interests you most:
- A) Source separation (Demucs integration)
- B) Enhanced VAD preprocessing (PyAnnote tuning)
- C) Post-processing filters (vocalization detection)
- D) Initial prompt engineering support
