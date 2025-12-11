# Test Media Quick Start Guide

**Purpose:** Quick reference for using standard test media samples in CP-WhisperX-App

---

## 📍 Standard Test Samples

### Sample 1: English Technical Content
- **File:** `in/Energy Demand in AI.mp4`
- **Size:** 14 MB
- **Language:** English
- **Best For:** Transcribe, Translate workflows
- **Complexity:** Low (clean audio, single speaker)

### Sample 2: Hinglish Bollywood Content
- **File:** `in/test_clips/jaane_tu_test_clip.mp4`
- **Size:** 28 MB
- **Language:** Hindi/Hinglish (code-mixed)
- **Best For:** Subtitle, Transcribe, Translate workflows
- **Complexity:** High (multiple speakers, music, cultural terms)

---

## 🚀 Quick Test Commands

### Testing Transcribe Workflow

```bash
# English technical content
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

# Hindi/Hinglish content
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe \
  --source-language hi
```

### Testing Translate Workflow

```bash
# English → Hindi
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow translate \
  --source-language en \
  --target-language hi

# Hindi → English
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language en

# Hindi → Spanish (non-Indic)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language es

# Hindi → Gujarati (Indic-to-Indic)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language gu
```

### Testing Subtitle Workflow

```bash
# Full subtitle generation (8 languages)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar

# Basic subtitle generation (English only)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en
```

---

## ✅ Quality Targets

### Sample 1 (English Technical)
- ✅ ASR Word Error Rate: ≤5%
- ✅ Translation BLEU Score: ≥90%
- ✅ Processing Time (first): <2 minutes
- ✅ Processing Time (cached): <30 seconds
- ✅ Technical terms preserved

### Sample 2 (Hinglish Bollywood)
- ✅ ASR Word Error Rate: ≤15%
- ✅ Subtitle Quality: ≥88%
- ✅ Context Awareness: ≥80%
- ✅ Glossary Application: 100%
- ✅ Subtitle Timing: ±200ms
- ✅ Character names preserved (Jai, Aditi, Meow)
- ✅ Cultural terms handled (beta, bhai, ji)

---

## 🧪 Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Tests for Specific Sample
```bash
# Sample 1 tests only
pytest tests/ -k sample_01

# Sample 2 tests only
pytest tests/ -k sample_02
```

### Run Specific Test Categories
```bash
# Workflow tests
pytest tests/test_workflow*.py

# Quality baseline tests
pytest tests/test_quality_baselines.py

# Caching tests
pytest tests/test_caching.py

# With coverage
pytest tests/ --cov
```

---

## 📊 Checking Results

### Expected Output Structure

**Transcribe Workflow:**
```
out/{date}/{user}/{job}/07_alignment/
├── transcript.txt                 # Plain text
├── transcript.json                # With timestamps
└── manifest.json                  # Processing metadata
```

**Translate Workflow:**
```
out/{date}/{user}/{job}/08_translate/
├── transcript_{target_lang}.txt
├── transcript_{target_lang}.json
├── translation_metadata.json
└── manifest.json
```

**Subtitle Workflow:**
```
out/{date}/{user}/{job}/10_mux/{media_name}/
├── {media_name}_subtitled.mkv     # With soft-embedded subtitles
├── subtitles/
│   ├── {media_name}.hi.srt
│   ├── {media_name}.en.srt
│   ├── {media_name}.gu.srt
│   ├── {media_name}.ta.srt
│   ├── {media_name}.es.srt
│   ├── {media_name}.ru.srt
│   ├── {media_name}.zh.srt
│   └── {media_name}.ar.srt
└── manifest.json
```

---

## 🔍 Validating Quality

### Check ASR Accuracy
```python
# Compare against reference transcript
from shared.quality_metrics import calculate_wer
wer = calculate_wer(reference_transcript, generated_transcript)
assert wer <= 0.05  # Sample 1
assert wer <= 0.15  # Sample 2
```

### Check Translation Quality
```python
# Calculate BLEU score
from shared.quality_metrics import calculate_bleu
bleu = calculate_bleu(reference_translation, generated_translation)
assert bleu >= 0.90  # Sample 1
assert bleu >= 0.85  # Sample 2
```

### Check Subtitle Timing
```python
# Validate timing accuracy
from shared.quality_metrics import check_subtitle_timing
timing_errors = check_subtitle_timing(subtitle_file, audio_file)
assert max(timing_errors) <= 200  # ±200ms
```

---

## 💾 Testing Caching

### First Run (No Cache)
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle --source-language hi --target-languages en

time ./run-pipeline.sh --job-dir out/{date}/{user}/{job1}
# Expected: ~10 minutes
```

### Second Run (With Cache)
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle --source-language hi --target-languages en

time ./run-pipeline.sh --job-dir out/{date}/{user}/{job2}
# Expected: ~30 seconds (95% faster)
```

### Disable Caching (Testing Fresh Run)
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle --source-language hi --target-languages en \
  --no-cache
```

---

## 🛠️ Troubleshooting

### Sample Files Not Found
```bash
# Verify files exist
ls -lh "in/Energy Demand in AI.mp4"
ls -lh "in/test_clips/jaane_tu_test_clip.mp4"

# Check test media index
cat in/test_media_index.json | jq '.test_samples[].file'
```

### Quality Targets Not Met
1. Check logs: `logs/pipeline_YYYYMMDD_HHMMSS.log`
2. Check stage manifests: `{job_dir}/{stage_dir}/manifest.json`
3. Validate configuration: `{job_dir}/.env.pipeline`
4. Check model versions match baseline
5. Review processing parameters

### Caching Not Working
```bash
# Check cache statistics
./tools/cache-manager.sh --stats

# Verify cache enabled
grep ENABLE_CACHING config/.env.pipeline

# Clear cache and retry
./tools/cache-manager.sh --clear all
```

---

## 📚 More Information

**Complete Documentation:**
- Test Media Index: `in/test_media_index.json`
- Developer Standards: `docs/developer/DEVELOPER_STANDARDS.md` § 1.4
- Architecture Roadmap: `docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md`
- Copilot Instructions: `.github/copilot-instructions.md`

**Testing Framework:**
- Test fixtures: `tests/conftest.py`
- Workflow tests: `tests/test_workflow*.py`
- Quality tests: `tests/test_quality_baselines.py`
- Caching tests: `tests/test_caching.py`

---

**Last Updated:** December 3, 2025  
**Version:** 1.0

---

**END OF QUICK START GUIDE**
