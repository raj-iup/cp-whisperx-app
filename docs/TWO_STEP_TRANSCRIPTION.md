# Two-Step Transcription + Translation Workflow

## Overview

The `--transcribe` mode with target language now uses a **two-step process** to generate and preserve both source and target language files.

## How It Works

### Step 1: Source Language Transcription
- Transcribes audio in **source language** (e.g., Hindi)
- Performs word-level alignment to source language
- Saves **source language files** without language suffix:
  - `{job_id}.srt`
  - `{job_id}.transcript.txt`
  - `{job_id}.segments.json`
  - `{job_id}.whisperx.json`

### Step 2: Target Language Translation
- Translates audio to **target language** (e.g., English)
- Performs word-level alignment to target language
- Saves **target language files** with language suffix:
  - `{job_id}-English.srt`
  - `{job_id}.transcript-English.txt`
  - `{job_id}-English.segments.json`
  - `{job_id}-English.whisperx.json`

## Command

```bash
./prepare-job.sh "in/movie.mp4" \
  --transcribe \
  --enable-silero-vad \
  --enable-pyannote-vad \
  -s hi \
  -t en \
  --start-time 00:10:00 \
  --end-time 00:15:00

./run_pipeline.sh -j <job-id>
```

## Output Structure

```
out/2025/11/15/1/20251115-0004/06_asr/
├── 20251115-0004.srt                       ← Hindi (source) subtitles
├── 20251115-0004.transcript.txt            ← Hindi (source) transcript
├── 20251115-0004.segments.json             ← Hindi (source) segments
├── 20251115-0004.whisperx.json             ← Hindi (source) full result
│
├── 20251115-0004-English.srt               ← English (target) subtitles
├── 20251115-0004.transcript-English.txt    ← English (target) transcript
├── 20251115-0004-English.segments.json     ← English (target) segments
├── 20251115-0004-English.whisperx.json     ← English (target) full result
│
├── transcript.json                          ← Standard format (target)
└── segments.json                            ← Standard format (target)
```

## Benefits

### 1. Quality Comparison
- Compare source and target transcripts side-by-side
- Verify translation accuracy
- Identify mistranslations or missed context

### 2. Debugging & Refinement
- Source transcript shows what was actually heard
- Target transcript shows translation quality
- Easy to pinpoint transcription vs translation issues

### 3. Multiple Uses
- Use source files for original language subtitles
- Use target files for translated subtitles
- Generate bilingual subtitles (future feature)
- Reuse source transcript for multiple target languages

### 4. Professional Workflow
- Standard in professional localization
- Audit trail for quality control
- Source of truth for retranslation

## Example Use Cases

### Bollywood to International
```bash
# Generate Hindi original + English translation
./prepare-job.sh "in/bollywood.mp4" -s hi -t en --transcribe
```

**Output**:
- Hindi transcripts (original dialogue)
- English transcripts (for international distribution)

### Anime Localization
```bash
# Generate Japanese original + English translation
./prepare-job.sh "in/anime.mp4" -s ja -t en --transcribe
```

**Output**:
- Japanese transcripts (for native speakers)
- English transcripts (for localization)

### Quality Verification
```bash
# Compare source vs target
diff out/.../06_asr/job.transcript.txt \
     out/.../06_asr/job.transcript-English.txt
```

## Log Output

When running the two-step process, you'll see:

```
============================================================
TWO-STEP TRANSCRIPTION + TRANSLATION
============================================================
STEP 1: Transcribing in source language...
  Task: transcribe (workflow_mode=transcribe-only, keeping source language)
  Audio duration: 300.0s (5.0 minutes)
  ...transcription process...
Saving source language files (hi)...
  Saved: 20251115-0004.whisperx.json
  Saved: 20251115-0004.segments.json
  Saved: 20251115-0004.transcript.txt
  Saved: 20251115-0004.srt
✓ Step 1 completed: Source language files saved

STEP 2: Translating to target language...
  Task: translate (workflow_mode=transcribe)
  Audio duration: 300.0s (5.0 minutes)
  ...translation process...
Saving target language files (en)...
  Saved: 20251115-0004-English.whisperx.json
  Saved: 20251115-0004-English.segments.json
  Saved: 20251115-0004.transcript-English.txt
  Saved: 20251115-0004-English.srt
✓ Step 2 completed: Target language files saved
============================================================
```

## Performance Impact

### Processing Time
- **Single-step** (old): ~4 minutes (direct translation)
- **Two-step** (new): ~5-6 minutes (transcribe + translate)
- **Overhead**: ~20-30% longer, but generates both sets of files

### Why the extra time?
- Step 1: Full transcription in source language
- Step 2: Full translation to target language
- Both steps include word-level alignment
- Model loads alignment models twice (once per language)

### Is it worth it?
**YES**, because you get:
- Source language files (for original subtitles)
- Target language files (for translated subtitles)
- Better quality control
- Professional workflow

## Technical Details

### Alignment Language
- **Step 1**: Aligns to source language (e.g., Hindi)
- **Step 2**: Aligns to target language (e.g., English)

This ensures accurate word-level timing for both languages.

### File Naming Convention
- **Source files**: No suffix (`job.srt`)
- **Target files**: Language suffix (`job-English.srt`)

### Standard Files
The pipeline still creates standard format files for downstream processing:
- `transcript.json` → Contains target language (for compatibility)
- `segments.json` → Contains target language (for compatibility)

## Single-Language Behavior

If you DON'T specify a target language:

```bash
./prepare-job.sh "in/movie.mp4" -s hi --transcribe
```

**Behavior**: Single-step transcription (original behavior)
- Only source language files generated
- No language suffix
- Faster processing

## Source-Only Mode

If source and target are the same:

```bash
./prepare-job.sh "in/movie.mp4" -s hi -t hi --transcribe
```

**Behavior**: Single-step transcription (no translation needed)
- Only one set of files
- No language suffix

## Comparison with Other Modes

### --transcribe (with target)
- Two-step: Source + Target
- Both sets preserved
- ~20-30% longer

### --transcribe-only
- Single-step: Source only
- No translation
- Faster (original speed)

### --translate-only
- Reuses existing transcript
- Translates only
- Requires prior transcription

## Future Enhancements

With both source and target files preserved, we can add:

1. **Bilingual Subtitles**
   - Display both languages simultaneously
   - Useful for language learning

2. **Retranslation**
   - Reuse source transcript for new target languages
   - Faster than full retranscription

3. **Quality Metrics**
   - Compare source vs target automatically
   - Flag potential translation issues

4. **Edit Source, Regenerate Target**
   - Fix source transcript
   - Regenerate target translation
   - Faster iteration

## Verification

Check both sets of files were created:

```bash
JOB_DIR="out/2025/11/15/1/20251115-0004/06_asr"

# Source files (no suffix)
ls -lh $JOB_DIR/*.srt | grep -v "English"
ls -lh $JOB_DIR/*.transcript.txt | grep -v "English"

# Target files (with suffix)
ls -lh $JOB_DIR/*-English.srt
ls -lh $JOB_DIR/*.transcript-English.txt
```

## Troubleshooting

### Only target files generated, no source files
- Check logs for "TWO-STEP TRANSCRIPTION" message
- Verify source and target languages are different
- Check `workflow_mode` is set to `transcribe`

### Both files have same content
- Translation may not have occurred
- Check source != target language
- Verify model supports translation for language pair

### Missing language suffix
- Source files never have suffix (by design)
- Only target files have language suffix
- Check you specified `-t` (target language)

---

**Date**: November 16, 2025
**Version**: 2.1.0
**Feature**: Two-step transcription with file preservation
