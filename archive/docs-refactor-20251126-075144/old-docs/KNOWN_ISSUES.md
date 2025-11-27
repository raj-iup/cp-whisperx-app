# Known Issues and Solutions

## Issue: Empty `05_pyannote_vad` Directory

### Description
After running a job, you may notice an empty `05_pyannote_vad/` directory in the job output:

```
out/2025/11/23/rpatel/4/
├── 05_pyannote_vad/          ← Empty directory
├── vad/                       ← Actual VAD results here
│   └── speech_segments.json
```

### Root Cause
This is a legacy directory structure artifact from an earlier pipeline design. The VAD (Voice Activity Detection) stage now outputs results to the `vad/` directory, but the numbered directory `05_pyannote_vad/` is still created for backwards compatibility.

### Impact
- **No functional impact** - VAD results are correctly stored in `vad/`
- Wastes minimal disk space (empty directory)
- May cause confusion when reviewing job output

### Solution

#### Option 1: Ignore (Recommended)
The empty directory is harmless and can be safely ignored. The pipeline correctly uses `vad/speech_segments.json`.

#### Option 2: Manual Cleanup
```bash
# Remove empty directory after job completes
rm -rf out/[job-path]/05_pyannote_vad/
```

#### Option 3: Pipeline Fix (For Developers)
To prevent creation of the empty directory, modify `scripts/run-pipeline.py`:

```python
# Find and comment out the directory creation line:
# (job_dir / "05_pyannote_vad").mkdir(exist_ok=True)
```

### Verification
Check that VAD results exist in the correct location:

```bash
# Should contain speech_segments.json
ls -la out/[job-path]/vad/

# Should have JSON with speech segments
cat out/[job-path]/vad/speech_segments.json | jq '.' | head
```

### Related
- VAD results are used by ASR stage for chunk boundaries
- Located at: `vad/speech_segments.json`
- Format: JSON array of `{start, end}` timestamps

---

## Issue: WhisperX Translation Environment Setup

### Description
When attempting to run WhisperX context-aware translation, you may encounter:

```
ModuleNotFoundError: No module named 'pythonjsonlogger'
```

### Root Cause
The WhisperX environment (`venv/whisperx`) is missing the `python-json-logger` dependency required by the shared logger module.

### Solution

#### Quick Fix
```bash
# Install missing dependency
venv/whisperx/bin/pip install python-json-logger

# Verify installation
venv/whisperx/bin/pip list | grep python-json-logger
```

#### Permanent Fix
Add to `requirements-whisperx.txt`:

```txt
# Logging
python-json-logger>=2.0.0
```

Then reinstall:
```bash
./install-whisperx.sh
```

### Verification
Test that WhisperX translation works:

```bash
python scripts/whisperx_translate_comparator.py out/[job-path] -v
```

Should output:
```
[INFO] Loading WhisperX large-v3 model...
[INFO] Running WhisperX with task='translate'...
```

---

## Issue: Directory Structure Confusion

### Description
Multiple directories with similar purposes may cause confusion:

```
job/
├── 05_pyannote_vad/       # Empty (legacy)
├── vad/                    # Actual VAD results
├── 99_source_separation/   # Source separation outputs
├── transcripts/            # ASR transcripts
└── subtitles/              # Final subtitles
```

### Clarification

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `vad/` | Voice Activity Detection | `speech_segments.json` |
| `05_pyannote_vad/` | Legacy (empty) | None - ignore |
| `99_source_separation/` | Audio separation | `vocals.wav`, `no_vocals.wav` |
| `transcripts/` | ASR output | `segments.json`, `segments_translated_*.json` |
| `subtitles/` | Final outputs | `*.srt` files, analysis |
| `media/` | Audio/video files | `audio.wav`, `*_clip.wav` |
| `logs/` | Pipeline logs | Stage-specific logs |

### Best Practice
Focus on these key output directories:
- `subtitles/` - Your final subtitle files
- `transcripts/segments.json` - Raw transcription data
- `logs/pipeline.log` - Main pipeline log

Ignore:
- `05_pyannote_vad/` - Empty legacy directory
- `99_source_separation/` - Intermediate audio (unless debugging)
- `vad/` - Internal VAD data (unless debugging)

---

## Issue: Translation Comparison Setup

### Description
Setting up all translation methods for comparison requires multiple environments.

### Solution

#### Automated Setup (Recommended)
The bootstrap script installs all required environments:

```bash
./bootstrap.sh
```

This installs:
- ✅ WhisperX (for context-aware translation)
- ✅ IndICTrans2 (for Indic language translation)
- ✅ NLLB (for multilingual translation)
- ✅ Common (for tools like Google Translate)

#### Manual Translation Generation

**Method 1: WhisperX Context-Aware**
```bash
# Requires: venv/whisperx with python-json-logger
python scripts/whisperx_translate_comparator.py out/[job-path] -v
# Output: *.en.whisperx.srt
```

**Method 2: Google Translate**
```bash
# Activate common environment
source venv/common/bin/activate
python scripts/retranslate_srt.py subtitles/movie.hi.srt \
  -o subtitles/movie.en.googletrans.srt \
  --method googletrans
```

**Method 3: IndICTrans2 (Automatic)**
```bash
# Runs automatically in subtitle pipeline for Indic languages
./run-pipeline.sh -j [job-id]
# Output: *.en.indictrans2.srt (if Hindi→English)
```

**Method 4: NLLB (Automatic)**
```bash
# Runs automatically in subtitle pipeline for non-Indic target languages
./run-pipeline.sh -j [job-id]
# Output: *.en.srt
```

### Verification
Check all translation outputs:

```bash
ls -lh out/[job-path]/subtitles/*.en*.srt

# Should see:
# movie.en.srt              (NLLB)
# movie.en.indictrans2.srt  (IndICTrans2)  
# movie.en.googletrans.srt  (Google Translate)
# movie.en.whisperx.srt     (WhisperX context-aware)
```

---

## Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Empty `05_pyannote_vad/` | Ignore - results in `vad/` |
| Missing `python-json-logger` | `venv/whisperx/bin/pip install python-json-logger` |
| WhisperX translation fails | Check environment: `ps aux \| grep whisperx` |
| Can't find VAD results | Look in `vad/speech_segments.json` not `05_*/` |
| Translation comparison incomplete | Run `whisperx_translate_comparator.py` |
| WhisperX hallucinations | Use IndICTrans2/NLLB instead - see below |

---

## Issue: WhisperX Translation Hallucinations

### Description
WhisperX direct translation (task='translate') can produce hallucinations, particularly during music/song segments where it gets stuck in repetition loops.

### Example
During song segments (03:45-04:00), WhisperX repeats "Okay" 20+ times instead of the actual dialogue.

**Expected**: "I'll tell you when I'm bored, okay?"  
**WhisperX Output**: "Okay. Okay. Okay..." (20+ repetitions)

### Root Cause
- Direct audio→translation without anti-hallucination features
- Music interferes with speech recognition
- No conditioning breaks cause repetition loops
- Token repetition during low-confidence segments

### Solution

#### Best Practice (Recommended)
Use the main pipeline instead of direct WhisperX translation:

```bash
# This avoids hallucinations:
./prepare-job.sh -i movie.mp4 -l hi -t en -w subtitle
./run-pipeline.sh out/[job-id]

# Produces:
# - movie.en.indictrans2.srt (text-based, no hallucinations)
# - movie.en.srt (NLLB, text-based)
```

**Why it works:**
- WhisperX only transcribes (task='transcribe')
- Translation from text (IndICTrans2/NLLB)
- Anti-hallucination features enabled
- Lyrics detection active
- Source separation removes music

#### For Existing WhisperX Translations
Compare with text-based translations:

```bash
# IndICTrans2 won't have hallucinations
diff movie.en.whisperx.srt movie.en.indictrans2.srt

# Use IndICTrans2 for song segments
# Use WhisperX for clean dialogue
```

### When to Use WhisperX Translation

**✅ Good for:**
- Clean dialogue (no music)
- Short clips (<5 min)
- English→Other languages
- Comparison/research

**❌ Avoid for:**
- Bollywood movies (music heavy)
- Long content (>30 min)
- Production use without review
- Song segments

### Detailed Documentation
See [WHISPERX_HALLUCINATIONS.md](./WHISPERX_HALLUCINATIONS.md) for:
- Detection methods
- Post-processing fixes
- Hybrid approaches
- Prevention strategies

---

## See Also

- [WhisperX Translation Guide](./WHISPERX_TRANSLATION_COMPARISON.md)
- [Hinglish Detection](./HINGLISH_DETECTION.md)
- [Pipeline Architecture](./technical/PIPELINE_ARCHITECTURE.md)
- [Troubleshooting Guide](./user-guide/troubleshooting.md)

---

**Last Updated**: November 24, 2025  
**Version**: 1.0.0
