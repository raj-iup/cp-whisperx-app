# IndicTrans2 Quickstart Guide - Hinglish to English + Multi-Language

**Fast, High-Quality Translation for Indic Languages (Hindi, Hinglish, Tamil, Telugu, Bengali, etc.)**

This guide shows you how to process Hinglish/Hindi content to English using IndicTrans2, plus generate additional subtitle tracks in other languages.

---

## Overview

**What is IndicTrans2?**
- Specialized AI model for translating 22 Indic languages → English
- 90% faster than Whisper for translation (3 min vs 46 min)
- Better quality for Indian content (names, places, cultural terms)
- Handles Hinglish (mixed Hindi-English) automatically

**Supported Source Languages:**
Hindi, Tamil, Telugu, Bengali, Gujarati, Kannada, Malayalam, Marathi, Punjabi, Urdu, Assamese, Odia, Nepali, Sindhi, Sinhala, Sanskrit, Kashmiri, Dogri, Manipuri, Konkani, Maithili, Santali

> **📚 Citation Notice**: This feature uses IndicTrans2 by AI4Bharat (Gala et al., 2023). If you use this in your work, please cite appropriately. See [CITATIONS.md](CITATIONS.md) for BibTeX and the citation section at the bottom of this guide.

---

## Example: Process Hinglish Movie

### Use Case: "Jaane Tu Ya Jaane Na 2008"
- **Input**: Hinglish audio (Hindi dialogue with English words mixed in)
- **Output**: English subtitles + Spanish, French, German, Japanese subtitles
- **Method**: IndicTrans2 for Hindi→English, then English→Others

---

## Step 1: Setup (One-time)

### Initial Bootstrap

IndicTrans2 is now **automatically installed** during bootstrap:

```bash
# Navigate to project directory
cd /Users/rpatel/Projects/cp-whisperx-app

# Run bootstrap (installs everything including IndicTrans2)
./scripts/bootstrap.sh

# Bootstrap will:
# ✓ Install all dependencies (including IndicTrans2)
# ✓ Prompt for HuggingFace authentication (required)
# ✓ Download and cache IndicTrans2 model (~2GB)
# ✓ Configure .env.pipeline with IndicTrans2 settings
# ✓ Ready for use immediately
```

### HuggingFace Authentication (Required)

⚠️ **IMPORTANT**: The IndicTrans2 model is **gated** and requires HuggingFace authentication:

**Step 1: Create HuggingFace Account**
```bash
# Visit https://huggingface.co/join
```

**Step 2: Request Model Access**
```bash
# Visit https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
# Click "Agree and access repository"
# Access is usually granted instantly
```

**Step 3: Authenticate**
```bash
# Login to HuggingFace
huggingface-cli login

# Enter your access token from https://huggingface.co/settings/tokens
# Choose: "y" to add token as git credential
```

**Step 4: Verify Authentication**
```bash
# Test IndicTrans2
python scripts/test_indictrans2.py
```

### Manual Installation (if needed)

If you've already run bootstrap but want to add IndicTrans2 later:

```bash
# Activate virtual environment
source .bollyenv/bin/activate

# Run IndicTrans2 installer
./install-indictrans2.sh

# Verify installation
python scripts/test_indictrans2.py
```

**Expected Output:**
```
✓ PyTorch configured correctly
✓ All dependencies installed
✓ IndicTrans2 model working
```

---

## Step 2: Process Hinglish → English (IndicTrans2)

### Method 1: Two-Step Workflow (Recommended for Multi-Language)

**Why Two-Step?**
- Transcribe once, translate many times
- 47-64% time savings for multiple languages
- Better quality control at each step

```bash
# Step 1: Transcribe Hindi audio to Hindi text (STEP 1)
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --transcribe-only \
  --source-language hi

# Run transcription
./run_pipeline.sh -j <job-id>

# Step 2: Translate Hindi text to English using IndicTrans2 (STEP 2)
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate-only \
  --source-language hi \
  --target-language en

# Run translation
./run_pipeline.sh -j <job-id>
```

**What Happens:**
```
STEP 1 (Transcribe-Only):
├─ WhisperX: Audio → Hindi text
├─ VAD: Voice activity detection
├─ Alignment: Word-level timestamps
└─ Output: segments.json (Hindi)

STEP 2 (Translate-Only):
├─ IndicTrans2: Hindi text → English text  ⚡ 90% faster!
├─ Alignment: Word-level timestamps (English)
├─ Speaker Diarization
└─ Output: English subtitles (.srt, .ass, .mp4)
```

### Method 2: One-Step Workflow (Quick & Easy)

```bash
# Single command for Hindi → English
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --source-language hi \
  --target-language en

# Run pipeline
./run_pipeline.sh -j <job-id>
```

**What Happens:**
```
Full Pipeline (15 stages):
├─ STEP 1: WhisperX transcribes Hindi audio → Hindi text
├─ STEP 2: IndicTrans2 translates Hindi text → English text  ⚡
├─ Alignment, diarization, subtitle generation
└─ Output: English subtitles + subtitled video
```

---

## Step 3: Generate Additional Languages

### Add Spanish, French, German, Japanese Subtitles

```bash
# Spanish subtitles (from English)
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate-only \
  --source-language en \
  --target-language es

./run_pipeline.sh -j <job-id>

# French subtitles (from English)
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate-only \
  --source-language en \
  --target-language fr

./run_pipeline.sh -j <job-id>

# German subtitles (from English)
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate-only \
  --source-language en \
  --target-language de

./run_pipeline.sh -j <job-id>

# Japanese subtitles (from English)
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate-only \
  --source-language en \
  --target-language ja

./run_pipeline.sh -j <job-id>
```

**Note:** For non-Indic languages, Whisper's translation is used (not IndicTrans2).

---

## Step 4: Find Your Output Files

```bash
# Output directory structure
out/
└── 2024-11-17_14-30-00/
    └── rpatel/
        └── jaane-tu-ya-jaane-na-2008_<timestamp>/
            ├── final/
            │   ├── Jaane Tu Ya Jaane Na 2008_subtitled.mp4  # Video with English subs
            │   └── Jaane Tu Ya Jaane Na 2008_subtitled.mkv  # With audio track
            ├── subtitles/
            │   ├── Jaane Tu Ya Jaane Na 2008.en.srt         # English subtitles
            │   ├── Jaane Tu Ya Jaane Na 2008.en.ass         # Styled subtitles
            │   ├── Jaane Tu Ya Jaane Na 2008.es.srt         # Spanish subtitles
            │   ├── Jaane Tu Ya Jaane Na 2008.fr.srt         # French subtitles
            │   ├── Jaane Tu Ya Jaane Na 2008.de.srt         # German subtitles
            │   └── Jaane Tu Ya Jaane Na 2008.ja.srt         # Japanese subtitles
            └── logs/
                └── pipeline.log                              # Processing logs
```

---

## Complete Example: Full Workflow

### Process Hinglish Movie to 5 Languages

```bash
#!/bin/bash
# Process "Jaane Tu Ya Jaane Na 2008" - Hinglish to 5 languages

MOVIE="in/Jaane Tu Ya Jaane Na 2008.mp4"

echo "=================================================="
echo "Processing: $MOVIE"
echo "Target Languages: English, Spanish, French, German, Japanese"
echo "=================================================="

# Step 1: Transcribe Hindi audio (do this once)
echo ""
echo "STEP 1: Transcribing Hindi audio..."
./prepare-job.sh "$MOVIE" --transcribe-only --source-language hi
JOB_ID=$(ls -t out/*/rpatel/ | head -1)
./run_pipeline.sh -j "$JOB_ID"

# Step 2: Translate Hindi → English (IndicTrans2 - 90% faster!)
echo ""
echo "STEP 2: Translating Hindi → English (via IndicTrans2)..."
./prepare-job.sh "$MOVIE" --translate-only --source-language hi --target-language en
JOB_ID=$(ls -t out/*/rpatel/ | head -1)
./run_pipeline.sh -j "$JOB_ID"

# Step 3: Translate English → Spanish
echo ""
echo "STEP 3: Translating English → Spanish..."
./prepare-job.sh "$MOVIE" --translate-only --source-language en --target-language es
JOB_ID=$(ls -t out/*/rpatel/ | head -1)
./run_pipeline.sh -j "$JOB_ID"

# Step 4: Translate English → French
echo ""
echo "STEP 4: Translating English → French..."
./prepare-job.sh "$MOVIE" --translate-only --source-language en --target-language fr
JOB_ID=$(ls -t out/*/rpatel/ | head -1)
./run_pipeline.sh -j "$JOB_ID"

# Step 5: Translate English → German
echo ""
echo "STEP 5: Translating English → German..."
./prepare-job.sh "$MOVIE" --translate-only --source-language en --target-language de
JOB_ID=$(ls -t out/*/rpatel/ | head -1)
./run_pipeline.sh -j "$JOB_ID"

# Step 6: Translate English → Japanese
echo ""
echo "STEP 6: Translating English → Japanese..."
./prepare-job.sh "$MOVIE" --translate-only --source-language en --target-language ja
JOB_ID=$(ls -t out/*/rpatel/ | head -1)
./run_pipeline.sh -j "$JOB_ID"

echo ""
echo "=================================================="
echo "✅ COMPLETE! Generated 5 subtitle tracks:"
echo "   1. English (from Hindi via IndicTrans2)"
echo "   2. Spanish (from English)"
echo "   3. French (from English)"
echo "   4. German (from English)"
echo "   5. Japanese (from English)"
echo "=================================================="
echo ""
echo "Find your files in: out/$(date +%Y-%m-%d)*/rpatel/jaane-tu-ya-jaane-na-2008*/"
```

Save as `process_hinglish_multi.sh` and run:
```bash
chmod +x process_hinglish_multi.sh
./process_hinglish_multi.sh
```

---

## Expected Timeline

### Processing Time (2-hour Hinglish movie)

| Step | Task | Time | Notes |
|------|------|------|-------|
| 1 | Transcribe Hindi | 35-40 min | WhisperX + VAD + alignment |
| 2 | Translate to English | **3-5 min** | ⚡ IndicTrans2 (90% faster!) |
| 3 | Spanish subtitles | 5-8 min | Whisper translation |
| 4 | French subtitles | 5-8 min | Whisper translation |
| 5 | German subtitles | 5-8 min | Whisper translation |
| 6 | Japanese subtitles | 5-8 min | Whisper translation |
| **Total** | **5 languages** | **~65 min** | **vs 200+ min (traditional)** |

**Time Savings: 67% faster than processing each language separately**

### Without Two-Step Workflow (Traditional Method)
- Each language: 40-46 min
- 5 languages: 200-230 min
- No IndicTrans2 benefit

---

## Performance Tips

### 1. Use Two-Step Workflow for Multiple Languages
```bash
# ✅ FAST: Transcribe once, translate many
./prepare-job.sh movie.mp4 --transcribe-only -s hi     # 40 min
./prepare-job.sh movie.mp4 --translate-only -s hi -t en  # 3 min (IndicTrans2!)
./prepare-job.sh movie.mp4 --translate-only -s en -t es  # 5 min
./prepare-job.sh movie.mp4 --translate-only -s en -t fr  # 5 min
# Total: 53 min for 3 languages

# ❌ SLOW: Full pipeline for each language
./prepare-job.sh movie.mp4 -s hi -t en  # 46 min
./prepare-job.sh movie.mp4 -s hi -t es  # 46 min
./prepare-job.sh movie.mp4 -s hi -t fr  # 46 min
# Total: 138 min for 3 languages
```

### 2. Enable Native GPU Acceleration
```bash
# Add --native flag for MPS (macOS) or CUDA (Linux/Windows)
./prepare-job.sh movie.mp4 --transcribe-only -s hi --native
```

### 3. Skip PyAnnote VAD for Speed
```bash
# 30% faster (less accurate speaker diarization)
./prepare-job.sh movie.mp4 --translate-only -s hi -t en --disable-pyannote-vad
```

### 4. Test with Short Clip First
```bash
# Process 5-minute clip to verify quality
./prepare-job.sh movie.mp4 --start-time 00:10:00 --end-time 00:15:00 -s hi -t en
```

---

## Understanding IndicTrans2

### Automatic Activation

IndicTrans2 is **automatically activated** by the pipeline when:

✅ **Source language is Indic** (Hindi, Tamil, Telugu, Bengali, etc.)  
✅ **Target language is English**  
✅ **IndicTrans2 is installed** (automatic via bootstrap)

**The pipeline intelligently selects the best translation method:**

```bash
# Hindi → English: Uses IndicTrans2 automatically
./prepare-job.sh movie.mp4 -s hi -t en
# Log: "✓ IndicTrans2 enabled for Hindi→English translation"

# Tamil → English: Uses IndicTrans2 automatically  
./prepare-job.sh movie.mp4 -s ta -t en
# Log: "✓ IndicTrans2 enabled for Tamil→English translation"

# English → Hindi: Uses Whisper (reverse direction not supported)
./prepare-job.sh movie.mp4 -s en -t hi
# Log: "Using Whisper translation"

# French → English: Uses Whisper (non-Indic source)
./prepare-job.sh movie.mp4 -s fr -t en
# Log: "Using Whisper translation"
```

### When is IndicTrans2 Used?

✅ **Automatically used for:**
- Hindi → English
- Tamil → English
- Telugu → English
- Bengali → English
- Any of 22 Indic languages → English

❌ **NOT used for:**
- English → Hindi (reverse direction)
- French → English (non-Indic source)
- Hindi → Spanish (non-English target, will be supported in future)

### How to Verify IndicTrans2 is Working

Check the pipeline logs:
```bash
# Look for this message in logs/pipeline.log
grep "Using IndicTrans2" out/*/rpatel/*/logs/pipeline.log
```

Expected output:
```
[2024-11-17 14:30:15] Using IndicTrans2 for hi→en translation
[2024-11-17 14:30:15] Source segments: 307
[2024-11-17 14:30:16] Loading IndicTrans2 model...
[2024-11-17 14:30:18] ✓ IndicTrans2 model loaded successfully
```

### Hinglish Handling

IndicTrans2 automatically detects and preserves English words in Hinglish:

**Input (Hinglish):**
```
"मुझे college जाना है और friends से मिलना है"
```

**Output (English):**
```
"I have to go to college and meet friends"
```

**Note:** English words like "college" and "friends" are preserved/translated naturally.

---

## Advanced: Custom Language Combinations

### Example: Tamil Movie to 4 Languages

```bash
# Tamil → English (via IndicTrans2)
./prepare-job.sh "tamil_movie.mp4" --transcribe-only -s ta
./prepare-job.sh "tamil_movie.mp4" --translate-only -s ta -t en

# English → Spanish, French, Japanese
./prepare-job.sh "tamil_movie.mp4" --translate-only -s en -t es
./prepare-job.sh "tamil_movie.mp4" --translate-only -s en -t fr
./prepare-job.sh "tamil_movie.mp4" --translate-only -s en -t ja
```

### Example: Auto-Detect Indic Language

```bash
# Let Whisper detect if it's Hindi, Tamil, or Telugu
./prepare-job.sh "indic_movie.mp4" --transcribe-only

# Check detected language in logs
grep "Detected language" out/*/rpatel/*/logs/pipeline.log

# Translate based on detected language
./prepare-job.sh "indic_movie.mp4" --translate-only -s <detected> -t en
```

---

## Troubleshooting

### Model Access / Authentication Errors

**Error:**
```
GatedRepoError: 401 Client Error
Access to model ai4bharat/indictrans2-indic-en-1B is restricted
You must have access to it and be authenticated to access it
```

**Fix:**
```bash
# Step 1: Request access to the model
# Visit: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
# Click: "Agree and access repository"
# Wait: Access is usually granted instantly

# Step 2: Authenticate with HuggingFace
huggingface-cli login
# Enter your token from: https://huggingface.co/settings/tokens

# Step 3: Verify authentication
python -c "from huggingface_hub import HfFolder; print('✓ Authenticated' if HfFolder.get_token() else '✗ Not authenticated')"

# Step 4: Re-run installer
./install-indictrans2.sh
```

### IndicTrans2 Not Available

**Error:**
```
⚠️ IndicTrans2 not available, falling back to Whisper translation
```

**Fix:**
```bash
pip install 'transformers>=4.44' sentencepiece sacremoses srt
python scripts/test_indictrans2.py
```

### Model Download Issues

**First run downloads ~2GB model:**
```bash
# Model cached to: ~/.cache/huggingface/
# If slow, set proxy or use mirror:
export HF_ENDPOINT=https://hf-mirror.com
```

### Translation Quality Issues

**For better quality:**
```bash
# Increase beam search (slower but better)
# Edit config/.env.pipeline:
INDICTRANS2_NUM_BEAMS=8  # default: 4
```

### Hinglish Not Detected Properly

**If too much English is being translated:**
```bash
# Adjust threshold in config/.env.pipeline:
INDICTRANS2_SKIP_ENGLISH_THRESHOLD=0.8  # default: 0.7 (70% English)
```

---

## Quick Reference Card

### Common Commands

```bash
# Hindi → English (IndicTrans2)
./prepare-job.sh movie.mp4 --transcribe-only -s hi
./prepare-job.sh movie.mp4 --translate-only -s hi -t en

# One-step (full pipeline)
./prepare-job.sh movie.mp4 -s hi -t en

# Check job status
./run_pipeline.sh -j <job-id> --status

# Resume failed job
./resume-pipeline.sh -j <job-id>

# View logs
tail -f out/*/rpatel/*/logs/pipeline.log

# Test IndicTrans2
python scripts/test_indictrans2.py
```

### Supported Indic Languages

| Code | Language | IndicTrans2 Code | Native Script |
|------|----------|------------------|---------------|
| hi   | Hindi    | hin_Deva | देवनागरी |
| ta   | Tamil    | tam_Taml | தமிழ் |
| te   | Telugu   | tel_Telu | తెలుగు |
| bn   | Bengali  | ben_Beng | বাংলা |
| gu   | Gujarati | guj_Gujr | ગુજરાતી |
| kn   | Kannada  | kan_Knda | ಕನ್ನಡ |
| ml   | Malayalam| mal_Mlym | മലയാളം |
| mr   | Marathi  | mar_Deva | मराठी |
| pa   | Punjabi  | pan_Guru | ਪੰਜਾਬੀ |
| ur   | Urdu     | urd_Arab | اردو |
| +12 more... | | | |

Full list: [INDICTRANS2_IMPLEMENTATION.md](INDICTRANS2_IMPLEMENTATION.md#language-support)

---

## Next Steps

- 📖 [Full IndicTrans2 Guide](INDICTRANS2_IMPLEMENTATION.md) - Technical details
- 🌍 [96-Language Guide](WORKFLOW_MODES_GUIDE.md) - All language combinations
- ⚙️ [Parameter Tuning](LANGUAGE_TUNING_QUICKREF.md) - Optimize quality
- 🚨 [Troubleshooting](QUICK_FIX_REFERENCE.md) - Common issues

---

## Summary

**Key Takeaways:**
1. ✅ IndicTrans2 is **90% faster** for Indic → English translation
2. ✅ Use **two-step workflow** for multiple languages (47-67% time savings)
3. ✅ Handles **Hinglish** automatically (preserves English words)
4. ✅ Supports **22 Indic languages** → English
5. ✅ Process once, generate **5+ subtitle tracks** efficiently

**Recommended Workflow:**
```
Hinglish Audio
    ↓ (Transcribe-Only, 40 min)
Hindi Text
    ↓ (Translate-Only, 3 min via IndicTrans2)
English Subtitles
    ↓ (Translate-Only, 5 min each)
Spanish, French, German, Japanese Subtitles
```

**Total Time: ~65 min for 5 languages** (vs 200+ min traditional method)

---

## Citation

**If you use IndicTrans2 in your work, please cite:**

```bibtex
@article{gala2023indictrans,
  title={IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22 Scheduled Indian Languages},
  author={Jay Gala and Pranjal A Chitale and A K Raghavan and Varun Gumma and Sumanth Doddapaneni and Aswanth Kumar M and Janki Atul Nawale and Anupama Sujatha and Ratish Puduppully and Vivek Raghavan and Pratyush Kumar and Mitesh M Khapra and Raj Dabre and Anoop Kunchukuttan},
  journal={Transactions on Machine Learning Research},
  issn={2835-8856},
  year={2023},
  url={https://openreview.net/forum?id=vfT4YuzAYA},
  note={}
}
```

**Resources:**
- 📄 **Paper**: [IndicTrans2 on OpenReview](https://openreview.net/forum?id=vfT4YuzAYA)
- 🤗 **Model**: [ai4bharat/indictrans2-indic-en-1B](https://huggingface.co/ai4bharat/indictrans2-indic-en-1B)
- 💻 **GitHub**: [AI4Bharat/IndicTrans2](https://github.com/AI4Bharat/IndicTrans2)
- 📚 **Full Citations**: [CITATIONS.md](CITATIONS.md)

---

*Last Updated: November 17, 2024*  
*Version: 2.0*
