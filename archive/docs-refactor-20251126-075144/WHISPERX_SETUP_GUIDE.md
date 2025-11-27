# WhisperX Translation Setup Guide

## Quick Setup (2 Steps)

### Step 1: Install Missing Dependency

```bash
# Install python-json-logger in WhisperX environment
venv/whisperx/bin/pip install python-json-logger

# Verify
venv/whisperx/bin/pip list | grep python-json-logger
```

### Step 2: Run Translation

```bash
# Generate WhisperX context-aware translation
python scripts/whisperx_translate_comparator.py out/[job-path] -v
```

**Expected output:**
```
[INFO] Loading WhisperX large-v3 model...
[INFO] Running WhisperX with task='translate'...
[INFO] ✓ Translation complete
[INFO] ✓ Created SRT: subtitles/movie.en.whisperx.srt
```

---

## What You Get

After running, you'll have:

```
subtitles/
├── movie.hi.srt                    # Original Hindi
├── movie.hi.tagged.srt             # Word-tagged Hinglish
├── movie.hi.analysis.json          # Language analysis
├── movie.en.srt                    # NLLB translation
├── movie.en.indictrans2.srt        # IndICTrans2 translation
├── movie.en.googletrans.srt        # Google Translate
└── movie.en.whisperx.srt           # ✨ WhisperX (context-aware)
```

---

## Why WhisperX Translation is Different

| Method | Input | Context | Best For |
|--------|-------|---------|----------|
| **WhisperX** | Audio | ✅ Audio + text | Natural speech, Hinglish |
| IndICTrans2 | Text | ❌ Text only | Formal Hindi, accuracy |
| NLLB | Text | ❌ Text only | General multilingual |
| Google Translate | Text | ❌ Text only | Quick comparison |

**WhisperX Advantages:**
- Hears tone, emphasis, prosody
- Better with code-switching (Hinglish)
- Uses speech patterns for meaning
- Single-pass (transcribe + translate)

---

## Complete Translation Workflow

### 1. Run Pipeline (Gets 2-3 translations)

```bash
# Prepare job
./prepare-job.sh -i movie.mp4 -l hi -t en -w subtitle

# Run subtitle pipeline  
./run-pipeline.sh out/[job-dir]
```

**Automatic outputs:**
- ✅ `movie.hi.srt` - Source Hindi
- ✅ `movie.hi.tagged.srt` - Hinglish detection
- ✅ `movie.en.srt` - NLLB translation
- ✅ `movie.en.indictrans2.srt` - IndICTrans2 (if available)

### 2. Add Google Translate (Optional)

```bash
source venv/common/bin/activate
python scripts/retranslate_srt.py \
  subtitles/movie.hi.srt \
  -o subtitles/movie.en.googletrans.srt \
  --method googletrans
```

### 3. Add WhisperX Translation (Context-Aware)

```bash
# One-time setup
venv/whisperx/bin/pip install python-json-logger

# Generate translation
python scripts/whisperx_translate_comparator.py out/[job-dir] -v
```

### 4. Compare All Translations

```bash
# View side-by-side
diff -y subtitles/movie.en.srt subtitles/movie.en.whisperx.srt

# Count differences
diff subtitles/movie.en.indictrans2.srt subtitles/movie.en.whisperx.srt | wc -l

# Word count comparison
for f in subtitles/*.en*.srt; do 
  echo "$f: $(wc -w < "$f") words"
done
```

---

## Troubleshooting

### Issue: Missing python-json-logger

**Error:**
```
ModuleNotFoundError: No module named 'pythonjsonlogger'
```

**Fix:**
```bash
venv/whisperx/bin/pip install python-json-logger
```

### Issue: Model Loading Fails

**Error:**
```
[ERROR] Failed to load WhisperX model
```

**Fix:**
```bash
# Check WhisperX environment
venv/whisperx/bin/python -c "import whisperx; print(whisperx.__version__)"

# Reinstall if needed
./install-whisperx.sh
```

### Issue: Translation Timeout

**Error:**
```
WhisperX translation timed out (30 minutes)
```

**Causes:**
- Audio file too long (>1 hour)
- CPU-only processing (no GPU/MPS)
- System resources exhausted

**Solutions:**
```bash
# Option 1: Process shorter clip
./prepare-job.sh -i movie.mp4 -l hi -t en \
  --start "00:05:00" --end "00:15:00"

# Option 2: Use existing transcription
# WhisperX can translate existing transcripts faster

# Option 3: Enable GPU if available
# Check device detection in logs
```

### Issue: Wrong Method Called

**Error:**
```
AttributeError: 'WhisperXProcessor' object has no attribute 'transcribe_and_translate'
```

**Fix:**
Already fixed in latest version. Update script:
```bash
git pull origin main
# Or manually fix scripts/whisperx_translate_comparator.py
```

### Issue: Empty Output

**Symptom:**
- Script completes but no `.whisperx.srt` file

**Check:**
```bash
# Verify JSON was created
ls -lh out/[job]/transcripts/segments_whisperx_translated.json

# Check logs
tail -100 /tmp/whisperx_final.log

# Manual SRT generation
python scripts/subtitle_gen.py \
  out/[job]/transcripts/segments_whisperx_translated.json \
  -o subtitles/movie.en.whisperx.srt
```

---

## Performance Optimization

### Speed Up Translation

**1. Use GPU/MPS if available:**
```bash
# Check current device
grep "Device:" /tmp/whisperx_final.log

# Should see:
# [INFO]   Active device: mps  (Mac)
# [INFO]   Active device: cuda (NVIDIA GPU)
# [INFO]   Active device: cpu  (slowest)
```

**2. Process shorter clips:**
```bash
# 5-10 minute clips are fastest
./prepare-job.sh -i movie.mp4 -l hi -t en \
  --clip --start "00:10:00" --end "00:15:00"
```

**3. Reduce batch size on low memory:**
Edit `scripts/whisperx_translate_comparator.py`:
```python
batch_size=16,  # Change to 8 or 4 if low memory
```

### Benchmark Times (6-minute audio)

| Device | Time | Speed |
|--------|------|-------|
| Apple M1 (MPS) | ~3 min | 2x realtime |
| NVIDIA RTX 3090 | ~1.5 min | 4x realtime |
| CPU (8-core) | ~12 min | 0.5x realtime |

---

## Integration with Pipeline

### Future: Automatic WhisperX Translation

Currently manual, but can be integrated into pipeline:

**Option A: Add to subtitle workflow**
```python
# In scripts/run-pipeline.py, after subtitle_generation_source:
if config.get("whisperx_translation", {}).get("enabled", False):
    subtitle_stages.append(("whisperx_translation", self._stage_whisperx_translation))
```

**Option B: Separate workflow**
```bash
# Add new workflow mode
./prepare-job.sh -i movie.mp4 -l hi -t en -w translation-compare

# Runs all translation methods automatically
```

---

## Comparison Methodology

### Qualitative Analysis

1. **Accuracy**: Does it match the audio meaning?
2. **Naturalness**: Does it read like native English?
3. **Context**: Does it understand Hinglish code-switching?
4. **Timing**: Are subtitles synced with speech?

### Example Comparison

**Hindi Original:**
> Sorry यह हमारी ग्रूप के लिए बहुत special गान है

**WhisperX (context-aware):**
> Sorry, this is a very special song for our group

**IndICTrans2 (text-only):**
> Sorry, this is a very special song for our group

**NLLB (text-only):**
> Sorry, this is a very special song for our group

**Google Translate:**
> Sorry this is a very special song for our group

**Analysis:**
- All similar for simple sentence
- WhisperX shines with ambiguous phrases, tone-dependent meaning
- Best tested on complex Hinglish dialogue with cultural references

---

## Best Practices

### When to Use Each Method

**Use WhisperX when:**
- High Hinglish code-switching
- Tone/emphasis changes meaning
- Natural conversation, slang
- You have GPU/MPS available

**Use IndICTrans2 when:**
- Formal Hindi content
- Need highest accuracy for Indic languages
- Batch processing many files
- Limited compute resources

**Use NLLB when:**
- Multiple target languages needed
- General multilingual content
- Baseline comparison

**Use Google Translate when:**
- Quick draft/comparison
- Testing subtitle timing
- Non-critical projects

### Recommended Workflow

1. **Generate all 3-4 translations**
2. **Review first 50 subtitles of each**
3. **Pick best method for bulk of content**
4. **Manual review/correction of key scenes**
5. **Use Hinglish detection to find problem areas**

---

## See Also

- [Hinglish Detection Guide](./HINGLISH_DETECTION.md)
- [Translation Comparison](./user-guide/TRANSLATION_COMPARISON.md)
- [WhisperX Translation Details](./WHISPERX_TRANSLATION_COMPARISON.md)
- [Known Issues](./KNOWN_ISSUES.md)

---

**Setup Time**: 2 minutes  
**Translation Time**: 3-15 minutes (depends on audio length, device)  
**Quality**: Best for natural speech and Hinglish content

🎯 **Quick Start**: `whisperx_translate_comparator.py out/[job] -v`
