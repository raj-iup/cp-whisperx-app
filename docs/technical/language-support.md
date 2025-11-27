# Language Support Matrix

**Last Updated:** 2024-11-20

## Overview

This document describes which language pairs are supported for transcription, translation, and subtitle generation.

## Transcription (ASR)

**Model:** WhisperX with large-v3  
**Direction:** Audio → Text (source language)

### Supported Languages

All languages supported by Whisper large-v3:

| Language | Code | Script | Accuracy |
|----------|------|--------|----------|
| **Hindi** | `hi` | Devanagari | Excellent |
| **Tamil** | `ta` | Tamil | Excellent |
| **Telugu** | `te` | Telugu | Excellent |
| **Bengali** | `bn` | Bengali | Excellent |
| **Gujarati** | `gu` | Gujarati | Excellent |
| **Kannada** | `kn` | Kannada | Excellent |
| **Malayalam** | `ml` | Malayalam | Excellent |
| **Marathi** | `mr` | Devanagari | Excellent |
| **Punjabi** | `pa` | Gurmukhi | Excellent |
| **Urdu** | `ur` | Arabic | Excellent |
| **English** | `en` | Latin | Excellent |
| **+90 more** | ... | Various | See Whisper docs |

**Usage:**
```bash
./prepare-job.sh in/audio.mp4 --transcribe -s hi
./prepare-job.sh in/audio.mp4 --transcribe -s ta
```

## Translation

### IndicTrans2 (Local, GPU-Accelerated)

**Models:**
- `indictrans2-indic-en-1B` (installed)
- `indictrans2-en-indic-1B` (not installed)

#### Supported Translation Pairs

| Source Language | Target Language | Method | Status | Notes |
|-----------------|-----------------|--------|--------|-------|
| **Any Indic** | **English** | Direct | ✅ **Works** | Single-step, high quality |
| Hindi (hi) | English (en) | Direct | ✅ Works | |
| Tamil (ta) | English (en) | Direct | ✅ Works | |
| Telugu (te) | English (en) | Direct | ✅ Works | |
| Bengali (bn) | English (en) | Direct | ✅ Works | |
| Gujarati (gu) | English (en) | Direct | ✅ Works | |
| **Any Indic** | **Another Indic** | Pivot (2-step) | ⚠️ **Partial** | Falls back to source |
| Hindi (hi) | Gujarati (gu) | hi→en→gu | ⚠️ Partial | Requires 2nd model |
| Tamil (ta) | Telugu (te) | ta→en→te | ⚠️ Partial | Requires 2nd model |
| **English** | **Any Indic** | Direct | ❌ **Not Available** | Requires 2nd model |

**Legend:**
- ✅ **Works:** Fully functional
- ⚠️ **Partial:** Returns source text (fallback)
- ❌ **Not Available:** Model not installed

### Detailed Language Support

#### Indic → English (Fully Supported) ✅

All 22 scheduled Indian languages:

```
Assamese (as)     → English (en) ✅
Bengali (bn)      → English (en) ✅
Gujarati (gu)     → English (en) ✅
Hindi (hi)        → English (en) ✅
Kannada (kn)      → English (en) ✅
Malayalam (ml)    → English (en) ✅
Marathi (mr)      → English (en) ✅
Odia (or)         → English (en) ✅
Punjabi (pa)      → English (en) ✅
Tamil (ta)        → English (en) ✅
Telugu (te)       → English (en) ✅
Urdu (ur)         → English (en) ✅
Nepali (ne)       → English (en) ✅
Sindhi (sd)       → English (en) ✅
Sinhala (si)      → English (en) ✅
Sanskrit (sa)     → English (en) ✅
Kashmiri (ks)     → English (en) ✅
Dogri (doi)       → English (en) ✅
Manipuri (mni)    → English (en) ✅
Konkani (kok)     → English (en) ✅
Maithili (mai)    → English (en) ✅
Santali (sat)     → English (en) ✅
```

**Usage:**
```bash
# Hindi audio → English subtitles
./prepare-job.sh in/hindi.mp4 --subtitle -s hi -t en

# Tamil audio → English subtitles
./prepare-job.sh in/tamil.mp4 --subtitle -s ta -t en
```

#### Indic → Indic (Partial Support) ⚠️

**Current Behavior:**
- Detection: ✅ Recognized
- Translation: ⚠️ Returns source text
- Logging: ✅ Clear warning message
- Pipeline: ✅ Completes successfully

**What you get:**
```bash
$ ./prepare-job.sh in/hindi.mp4 --subtitle -s hi -t gu

Output:
  ✅ Hindi transcript (source)
  ⚠️ "Gujarati" subtitles with Hindi text
  
Log:
  [WARNING] IndicTrans2 requires two-step translation for hi→gu
  [INFO] Returning source text unchanged
```

**Examples:**
```
Hindi (hi)    → Gujarati (gu)   ⚠️ Partial
Hindi (hi)    → Tamil (ta)      ⚠️ Partial
Tamil (ta)    → Telugu (te)     ⚠️ Partial
Bengali (bn)  → Marathi (mr)    ⚠️ Partial
```

**To enable full support:**
```bash
# Install second model (future enhancement)
pip install indictrans2-en-indic
# Storage: Additional ~2GB
```

#### English → Indic (Not Available) ❌

**Status:** Requires `indictrans2-en-indic-1B` model (not installed)

**Examples:**
```
English (en) → Hindi (hi)      ❌ Not available
English (en) → Tamil (ta)      ❌ Not available
English (en) → Gujarati (gu)   ❌ Not available
```

**Workaround:** Use external service (Google Translate, etc.)

## Subtitles

### Generation

**Format:** SRT (SubRip Text)  
**Encoding:** UTF-8  
**Embedding:** Soft subtitles in MP4/MKV

### Supported Subtitle Tracks

| Type | Language | Status | Notes |
|------|----------|--------|-------|
| **Source** | Same as audio | ✅ Always | Original language |
| **English** | en | ✅ If requested | High-quality translation |
| **Other Indic** | hi,ta,gu,etc | ⚠️ Partial | Falls back to source |

### Multi-Language Subtitles

**Example:**
```bash
# Hindi audio → English + Gujarati + Tamil subtitles
./prepare-job.sh in/hindi.mp4 --subtitle -s hi -t en,gu,ta
```

**Result:**
```
Video with 4 subtitle tracks:
  1. Hindi (hi)    - Source language ✅
  2. English (en)  - Translated ✅
  3. Gujarati (gu) - Source text (Hindi) ⚠️
  4. Tamil (ta)    - Source text (Hindi) ⚠️
```

**Log output:**
```
[INFO] Translating to EN... ✓
[WARNING] hi→gu requires two models (using source)
[WARNING] hi→ta requires two models (using source)
[INFO] Generated 4 subtitle tracks
```

## Workflows

### Workflow 1: Transcribe Only

**Supported:** All Whisper languages

```bash
# Hindi audio → Hindi transcript
./prepare-job.sh in/audio.mp4 --transcribe -s hi

# Output: Hindi text file
```

### Workflow 2: Translate to English

**Supported:** All Indic languages → English

```bash
# Hindi audio → English transcript
./prepare-job.sh in/audio.mp4 --translate -s hi -t en

# Output: English text file
```

### Workflow 3: Multi-Language Subtitles

**Supported:** Source + English + Others (partial)

```bash
# Hindi audio → Hindi + English + Gujarati subtitles
./prepare-job.sh in/audio.mp4 --subtitle -s hi -t en,gu

# Output:
#   ✅ Hindi subtitles (source)
#   ✅ English subtitles (translated)
#   ⚠️ Gujarati subtitles (source text - Hindi)
```

## Recommendations

### For Best Results

**✅ Recommended combinations:**
```bash
# Any Indic → English
--subtitle -s hi -t en        ✅ Excellent
--subtitle -s ta -t en        ✅ Excellent
--subtitle -s bn -t en        ✅ Excellent

# Source + English
--subtitle -s hi -t en        ✅ Two tracks: hi, en
--subtitle -s ta -t en        ✅ Two tracks: ta, en
```

**⚠️ Partially supported:**
```bash
# Indic → Indic (returns source)
--subtitle -s hi -t gu        ⚠️ Partial (Hindi text in both)
--subtitle -s ta -t te        ⚠️ Partial (Tamil text in both)

# Multiple Indic targets
--subtitle -s hi -t gu,ta,te  ⚠️ Partial (Hindi text in all)
```

**❌ Not recommended:**
```bash
# English → Indic (not supported)
--subtitle -s en -t hi        ❌ Will fail
--subtitle -s en -t ta        ❌ Will fail
```

### Use Cases

#### Use Case 1: Bollywood Movie with English Subtitles

```bash
# Hindi audio → Hindi + English subtitles
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en --start-time 00:10:00 --end-time 00:15:00

✅ Perfect! High-quality English translation
```

#### Use Case 2: South Indian Content

```bash
# Tamil audio → Tamil + English subtitles
./prepare-job.sh in/movie.mp4 --subtitle -s ta -t en

✅ Perfect! Tamil preserved, English added
```

#### Use Case 3: Multi-Regional Distribution

```bash
# Hindi audio → Hindi + English + Gujarati + Tamil
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu,ta

⚠️ Partial:
  • hi: Original ✅
  • en: Translated ✅
  • gu: Hindi text (not translated) ⚠️
  • ta: Hindi text (not translated) ⚠️

Better approach: Generate English, use external service for gu/ta
```

## Future Enhancements

### Planned Features

1. **Full Indic→Indic support**
   - Install `indictrans2-en-indic-1B` model
   - Implement two-step pivot translation
   - Storage: +2GB
   - ETA: Next release

2. **External translation services**
   - Google Translate API integration
   - DeepL API integration
   - Fallback chain: IndicTrans2 → Google → DeepL

3. **Caching and optimization**
   - Cache intermediate translations (English pivot)
   - Reuse translations across jobs
   - Reduce redundant API calls

4. **Quality metrics**
   - BLEU scores
   - User ratings
   - Confidence intervals

## Configuration

### Enable Debug Logging

```bash
./prepare-job.sh in/audio.mp4 --subtitle -s hi -t en,gu --debug
```

**Output includes:**
```
[DEBUG] Language pair: hi → en (direct) ✅
[DEBUG] Language pair: hi → gu (pivot required) ⚠️
[DEBUG] Using fallback: source text for gu
```

### Check Language Support

```bash
# List supported source languages (transcription)
cat docs/LANGUAGE_SUPPORT_MATRIX.md | grep -A 50 "Supported Languages"

# Check translation capabilities
cat docs/LANGUAGE_SUPPORT_MATRIX.md | grep -A 50 "Translation Pairs"
```

## Troubleshooting

### Issue: Translation Not Working

**Problem:** Target language shows source text

**Diagnosis:**
```bash
# Check logs
tail -100 out/*/logs/99_indictrans2_*.log

# Look for:
[WARNING] IndicTrans2 does not support X→Y
```

**Solution:**
- If Indic→English: Check model installation
- If Indic→Indic: Expected behavior (not supported yet)
- If English→Indic: Not supported (use external service)

### Issue: Wrong Language Detected

**Problem:** Whisper detects wrong source language

**Solution:**
```bash
# Always specify source language explicitly
./prepare-job.sh in/audio.mp4 --subtitle -s hi -t en
#                                           ^^^^
#                                      Explicit source
```

### Issue: Poor Translation Quality

**Problem:** Translation doesn't make sense

**Diagnosis:**
- Check source transcription accuracy first
- If source transcript is wrong, translation will be wrong

**Solution:**
```bash
# Step 1: Test transcription only
./prepare-job.sh in/audio.mp4 --transcribe -s hi

# Step 2: Review transcript
cat out/*/transcripts/transcript_hi.txt

# Step 3: If transcript is good, then translate
./prepare-job.sh in/audio.mp4 --translate -s hi -t en
```

## Summary

| Language Pair | Support Level | Recommendation |
|---------------|---------------|----------------|
| **Indic → English** | ✅ Excellent | Use for production |
| **Indic → Indic** | ⚠️ Partial | Wait for full support or use external service |
| **English → Indic** | ❌ Not available | Use external translation service |
| **Any → English** | ✅ Good | Whisper built-in translation |

**Best Practice:**
```bash
# For production: Stick with Indic→English
./prepare-job.sh in/content.mp4 --subtitle -s hi -t en

# For experimental: Try multiple targets (know limitations)
./prepare-job.sh in/content.mp4 --subtitle -s hi -t en,gu --debug
```

---

**See also:**
- `docs/FIX_INDIC_TO_INDIC_TRANSLATION.md` - Technical details
- `config/.env.pipeline` - Configuration options
- `README.md` - Quick start guide
