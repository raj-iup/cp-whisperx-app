# Scene Selection Tips for Better Transcription

## Your Current Issue
The clip from **1:30 to 5:30** of "Jaane Tu Ya Jaane Na 2008" may contain:
- Opening credits with background music
- Minimal dialogue
- Mostly non-speech content

**Evidence**: VAD detected only 22 speech segments over 4 minutes (~5.5 segments per minute), indicating sparse dialogue.

## Good Scenes for Testing

### What Makes a Good Test Clip?
✅ **Active dialogue** between characters  
✅ **Clear speech** with minimal background music  
✅ **Multiple speakers** for testing speaker diarization  
✅ **2-5 minutes duration** (manageable, fast testing)  
❌ **Avoid**: Opening credits, songs, action sequences  

### Recommended Time Ranges to Try

For "Jaane Tu Ya Jaane Na 2008", try these alternatives:

```bash
# Scene with conversation (example - adjust based on actual content)
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:15:00" --end "00:18:00" \
                 --source-lang hi --target-langs en,gu

# Another dialogue-heavy scene
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:25:00" --end "00:28:00" \
                 --source-lang hi --target-langs en,gu

# Character interaction scene
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:35:00" --end "00:38:00" \
                 --source-lang hi --target-langs en,gu
```

## How to Find Good Scenes

### Method 1: Quick Preview
```bash
# Play the movie and note timestamps with dialogue
vlc "in/Jaane Tu Ya Jaane Na 2008.mp4"

# Look for:
# - Scenes where characters are talking
# - Indoor scenes (usually clearer audio)
# - Dialogue scenes (not songs or background music)
```

### Method 2: Check Audio Waveform
```bash
# Extract audio and visualize
ffmpeg -i "in/Jaane Tu Ya Jaane Na 2008.mp4" -vn -ss 00:01:30 -t 240 test_audio.wav
# Use audio editor (Audacity, etc.) to see where speech occurs
```

### Method 3: VAD Pre-Check
Run VAD on a longer segment to find speech-dense regions:
```bash
# Check the full movie's speech pattern
# (This would require a custom script - contact if needed)
```

## Common Pitfalls

### 1. **Opening Credits (0:00 - ~5:00)**
- Usually just music and titles
- Minimal or no dialogue
- Not good for transcription testing

### 2. **Song Sequences**
- Background music dominates
- Lyrics might be transcribed but not actual dialogue
- Use for music transcription testing only

### 3. **Action Scenes**
- Loud sound effects
- Minimal dialogue
- Poor SNR (Signal-to-Noise Ratio)

### 4. **Crowd/Background Noise**
- Multiple overlapping speakers
- Hard for ASR models
- Better for advanced diarization testing

## Ideal Scene Characteristics

| Factor | Ideal Value | Why |
|--------|-------------|-----|
| **Dialogue density** | >15 segments/min | Enough content to test |
| **Background music** | Low/Medium | Clear speech priority |
| **Number of speakers** | 2-4 | Good for diarization |
| **Speech clarity** | High | Better accuracy baseline |
| **Duration** | 2-5 minutes | Fast iteration |

## Testing Workflow

### Step 1: Quick Audio Check
```bash
# Extract and listen to a test segment
ffmpeg -i "in/Jaane Tu Ya Jaane Na 2008.mp4" \
       -ss 00:15:00 -t 180 \
       -vn test_clip.wav

# Play and verify clear dialogue
afplay test_clip.wav  # macOS
# aplay test_clip.wav  # Linux
```

### Step 2: Run Transcription
```bash
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:15:00" --end "00:18:00" \
                 --source-lang hi --target-langs en,gu

./run-pipeline.sh
```

### Step 3: Verify Results
```bash
# Check segment diversity
jq -r '.segments[].text' out/*/transcripts/segments.json | head -10

# Should show varied dialogue, not repeated text
```

### Step 4: Iterate if Needed
If still getting issues:
1. Try a different scene with more dialogue
2. Check if the source audio is clear
3. Consider using a smaller model (medium) for faster testing
4. Review VAD output to confirm speech is present

## Other Movies to Try

If "Jaane Tu Ya Jaane Na" scenes are difficult:

```bash
# Try other movies with clear dialogue
./prepare-job.sh --media "Laawaris_1981.mp4" \
                 --start "00:10:00" --end "00:13:00" \
                 --source-lang hi --target-langs en,gu

./prepare-job.sh --media "Satte_Pe_Satta_(1982).mp4" \
                 --start "00:20:00" --end "00:23:00" \
                 --source-lang hi --target-langs en,gu
```

## Pro Tips

1. **Start with known good scenes**: Re-watch a favorite scene and use that
2. **Use shorter clips initially**: 2-3 minutes for fast feedback
3. **Check VAD output first**: High segment count = good dialogue density
4. **Multiple speakers**: Better for testing full pipeline (ASR + diarization)
5. **Avoid first 5 minutes**: Usually credits and intro sequences

## Summary

Your 1:30-5:30 clip likely has **minimal dialogue**. Try:
- ✅ **Scenes from 10-60 minutes** into the movie (main content)
- ✅ **Conversation scenes** between characters
- ✅ **Indoor scenes** with clear audio
- ❌ **Avoid opening credits, songs, action sequences**

---
**Next Action**: Pick a dialogue-heavy scene and re-test with the anti-hallucination fix!
