# CP-WhisperX-App

**Multi-Language Subtitle Generation Pipeline with 96+ Language Support**

Transform any video into professional subtitles with context-aware translation, speaker diarization, and intelligent bias prompting. Built for Bollywood content, now supporting international films, anime, documentaries, and more.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()
[![Languages](https://img.shields.io/badge/languages-96-brightgreen.svg)](docs/WORKFLOW_MODES_GUIDE.md)

---

## 🎯 What This Does

**Input**: Video in ANY of 96 languages (Hindi, Spanish, Japanese, French, etc.)  
**Output**: Professional subtitles with speaker labels, cultural context, and perfect timing

**Key Innovation**: Transcribe once, translate to multiple languages efficiently (27-36% time savings)

---

## ✨ What's New (v2.0)

### 🌍 Multi-Language Support
- **96 Languages**: ANY-TO-ANY language combinations
- **4 Workflow Modes**: Optimized for different use cases
- **27-36% Faster**: Transcribe once, translate many times
- **Auto-Detection**: Automatic source language identification

### 🇮🇳 IndicTrans2 Integration (NEW!)
- **22 Indic Languages**: Specialized support for Hindi, Tamil, Telugu, Bengali, and 18 more
- **90% Faster**: Hindi→English translation in 3 min vs 46 min with Whisper
- **Better Quality**: Superior translation for Indian names, places, and cultural terms
- **Hinglish Support**: Automatically preserves English words in mixed content
- **Auto-Activated**: Automatically used when source is Indic and target is English

**Quick Example:**
```bash
# Spanish to English
./prepare-job.sh movie.mp4 --transcribe-only -s es
./prepare-job.sh movie.mp4 --translate-only -s es -t en

# Hindi to English (IndicTrans2 automatically activated - 90% faster!)
./prepare-job.sh movie.mp4 --transcribe-only -s hi
./prepare-job.sh movie.mp4 --translate-only -s hi -t en

# Japanese to 3 languages (47% time savings!)
./prepare-job.sh anime.mp4 --transcribe-only -s ja
./prepare-job.sh anime.mp4 --translate-only -s ja -t en
./prepare-job.sh anime.mp4 --translate-only -s ja -t es
./prepare-job.sh anime.mp4 --translate-only -s ja -t fr
```

📖 **[Complete Multi-Language Guide](docs/WORKFLOW_MODES_GUIDE.md)** - 96 languages, real-world use cases, performance tips  
🇮🇳 **[IndicTrans2 Quickstart](docs/INDICTRANS2_QUICKSTART.md)** - Fast Indic language processing

---

## 🚀 Quick Start

Get your first subtitles in 5 minutes:

```bash
# 1. Clone and setup (downloads all ML models automatically)
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app
./scripts/bootstrap.sh

# 2. Check model status (optional)
./check-models.sh

# 3. Process a video (default: Hindi → English)
./prepare-job.sh /path/to/movie.mp4
./run_pipeline.sh -j <job-id>

# 4. Get your subtitled video
# Output: out/<date>/<user>/<job-id>/final/<movie>_subtitled.mp4
```

📖 **[Detailed Setup Guide](docs/QUICKSTART.md)** - Step-by-step with screenshots

---

## 📚 Documentation

**Quick Access:**
- 📖 **[Documentation Index](docs/INDEX.md)** - Complete documentation navigation
- 🚀 **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- 🌍 **[Multi-Language Guide](docs/WORKFLOW_MODES_GUIDE.md)** - 96 languages, workflow modes
- 🤖 **[Model Management](docs/MODEL_MANAGEMENT.md)** - Check & download ML models
- 🇮🇳→🇬🇧 **[IndicTrans2 Guide](docs/INDICTRANS2_QUICKSTART.md)** - Fast Hindi→English translation
- ⚙️ **[Parameter Tuning](docs/LANGUAGE_TUNING_QUICKREF.md)** - Optimize for any language
- 📚 **[Citations](docs/CITATIONS.md)** - Academic references

**Quick References:**
- [Two-Step Transcription](docs/QUICK_REFERENCE_TWO_STEP.md)
- [IndicTrans2 Reference](docs/INDICTRANS2_REFERENCE.md)
- [Language Parameter Quick Ref](docs/LANGUAGE_TUNING_QUICKREF.md)
- [Troubleshooting](docs/QUICK_FIX_REFERENCE.md)

---

## 🎬 Use Cases

### International Film Distribution
**Scenario**: Release Spanish film globally  
**Solution**: Transcribe once, generate 4+ subtitle tracks  
**Time**: 220% vs 400% (45% savings)

### Anime Localization
**Scenario**: Japanese anime for multiple markets  
**Solution**: 6 language versions from one transcription  
**Time**: 280% vs 600% (53% savings)

### Bollywood International
**Scenario**: Hindi movies for global audiences  
**Solution**: English, Spanish, French, Arabic, Chinese subtitles  
**Benefit**: Maintain cultural nuances with glossary system

### Documentary Localization
**Scenario**: Educational content in 7+ languages  
**Solution**: Efficient multi-language generation  
**Benefit**: Consistent quality across all languages

📖 **[More Use Cases](docs/WORKFLOW_MODES_GUIDE.md#real-world-use-cases)** - 6 detailed scenarios

---

## ⚡ Key Features

### 🌍 Multi-Language Support (96+ Languages)

<details>
<summary><strong>Supported Languages</strong> (click to expand)</summary>

**South Asian**: Hindi, Urdu, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Sindhi, Nepali, Sinhala

**European**: English, Spanish, French, German, Italian, Portuguese, Russian, Dutch, Polish, Ukrainian, Czech, Romanian, Swedish, Danish, Norwegian, Finnish, Greek, and 20+ more

**East Asian**: Japanese, Korean, Chinese, Cantonese, Burmese, Lao, Khmer

**Middle Eastern**: Arabic, Turkish, Persian, Hebrew, Azerbaijani, Kazakh, Uzbek, Kyrgyz, Tajik, Turkmen

**Southeast Asian**: Vietnamese, Indonesian, Malay, Thai, Tagalog, Javanese

**African**: Swahili, Yoruba, Hausa, Zulu, Afrikaans, Amharic, Somali

**Other**: Mongolian, Armenian, Georgian, Tibetan, Latin, Sanskrit, Hawaiian, and more

**Special**: Auto-detect (Whisper identifies language automatically)

📖 **[Complete Language Reference](docs/WORKFLOW_MODES_GUIDE.md#supported-languages)**
</details>

### 🔄 4 Optimized Workflow Modes

| Mode | Languages | Stages | Time | Output | Best For |
|------|-----------|--------|------|--------|----------|
| **subtitle-gen** | ANY → ANY (default: hi→en) | 15 | 100% | Video + embedded subs | Single subtitled video |
| **transcribe-only** | ANY | 6 | 40% | segments.json | Prepare for multi-language |
| **translate-only** | ANY → ANY | 9 | 60% | Target language subs | Multiple subtitle tracks |
| **transcribe** | ANY | 3-5 | 20% | Transcripts + video clip | Quick testing, fast dialogues |

**Example Workflows:**
```bash
# subtitle-gen: Spanish to English (full pipeline with video)
./prepare-job.sh movie.mp4 -s es -t en

# Multi-language: Transcribe once, translate to multiple languages
./prepare-job.sh movie.mp4 --transcribe-only -s es
./prepare-job.sh movie.mp4 --translate-only -s es -t en  # English
./prepare-job.sh movie.mp4 --translate-only -s es -t fr  # French
./prepare-job.sh movie.mp4 --translate-only -s es -t de  # German

# transcribe: Fast dialogues with dual VAD (Bollywood Hinglish example)
./prepare-job.sh movie.mp4 --transcribe --enable-silero-vad --enable-pyannote-vad -s hi

# transcribe with translation: Generate both Hindi transcription AND English translation
./prepare-job.sh movie.mp4 --transcribe --enable-silero-vad --enable-pyannote-vad -s hi -t en
```

📖 **[Workflow Modes Guide](docs/WORKFLOW_MODES_GUIDE.md)**

### 🚀 IndicTrans2: High-Quality Hindi→English Translation (NEW!)

**93% faster, better quality** specialized translation for Hindi content using [IndicTrans2](https://openreview.net/forum?id=vfT4YuzAYA) by AI4Bharat:

- **Speed**: 3 minutes vs 46 minutes for 2.5 hour movie (STEP 2 only)
- **Quality**: AI4Bharat's specialized model for Indian languages
- **Smart**: Handles Hinglish (mixed Hindi-English) automatically
- **Seamless**: Works automatically when translating Hindi→English
- **Fallback**: Uses Whisper if unavailable

**Setup:**
```bash
./install-indictrans2.sh
```

**Automatic Usage:**
```bash
# Transcribe Hindi movie, translate to English
./prepare-job.sh movie.mp4 -s hi -t en
# IndicTrans2 automatically used for translation!
```

📖 **[IndicTrans2 Documentation](docs/INDICTRANS2_QUICKSTART.md)** | 📚 **[Citations](docs/CITATIONS.md)**

### ⚙️ Language-Specific Parameter Tuning

**Automatic quality optimization** for all language pairs:

For **Hindi↔English**: Uses IndicTrans2 + standard parameters (fast)  
For **all other languages**: Automatically applies enhanced Whisper parameters (better quality)

**Enhanced parameters** (auto-applied for non-Hindi/English):
```bash
WHISPER_TEMPERATURE=0.0            # More deterministic
WHISPER_BEAM_SIZE=10               # Broader search (default: 5)
WHISPER_NO_SPEECH_THRESHOLD=0.7    # Stricter silence (default: 0.6)
WHISPER_LOGPROB_THRESHOLD=-0.5     # Higher quality (default: -1.0)
```

**Override per job** by editing `.env` file in output directory.

📖 **[Parameter Tuning Guide](docs/LANGUAGE_PARAMETER_TUNING.md)**

<details>
<summary><strong>Advanced: Dual VAD for Fast Dialogues</strong> (click to expand)</summary>

For content with rapid dialogue changes between multiple speakers (Bollywood movies, animated shows, interviews), use **--transcribe** with both VAD stages:

**4-Stage Pipeline: Demux → Silero VAD → PyAnnote VAD → ASR**

```bash
# Bollywood Hinglish with fast dialogues (transcription only)
./prepare-job.sh /path/to/movie.mp4 \
  --transcribe \
  --enable-silero-vad \
  --enable-pyannote-vad \
  --source-language hi

# With translation to English (generates both languages)
./prepare-job.sh /path/to/movie.mp4 \
  --transcribe \
  --enable-silero-vad \
  --enable-pyannote-vad \
  --source-language hi \
  --target-language en

# With GPU acceleration (faster)
./prepare-job.sh /path/to/movie.mp4 \
  --transcribe \
  --enable-silero-vad \
  --enable-pyannote-vad \
  --source-language hi \
  --target-language en \
  --native

# Test on 5-minute clip first
./prepare-job.sh /path/to/movie.mp4 \
  --transcribe \
  --enable-silero-vad \
  --enable-pyannote-vad \
  --source-language hi \
  --target-language en \
  --start-time 00:10:00 \
  --end-time 00:15:00
```

**Output Files** (with two-step transcription + translation):
```
out/2025/11/15/1/20251115-0004/
├── 06_asr/
│   ├── 20251115-0004.srt                       # Source language (Hindi) subtitles
│   ├── 20251115-0004.transcript.txt            # Source language (Hindi) transcript
│   ├── 20251115-0004.segments.json             # Source language segments
│   ├── 20251115-0004.whisperx.json             # Source language full result
│   ├── 20251115-0004-English.srt               # Target language (English) subtitles
│   ├── 20251115-0004.transcript-English.txt    # Target language (English) transcript
│   ├── 20251115-0004-English.segments.json     # Target language segments
│   ├── 20251115-0004-English.whisperx.json     # Target language full result
│   ├── transcript.json                          # Standard format (target language)
│   └── segments.json                            # Standard format (target language)
└── 07_create_clip/
    └── Jaane Tu Ya Jaane Na 2008-English_subtitled.mp4  # Video clip with embedded subs
```

**Two-Step Processing** (keeps both source and target files):
1. **Step 1**: Transcribe in source language (Hindi) → Save Hindi files
2. **Step 2**: Translate to target language (English) → Save English files
   - Both sets of files are preserved in the output directory
   - Allows comparison and quality verification

**5-Stage Pipeline** (with dual VAD + video clip):
1. **Demux** - Extract audio from video
2. **Silero VAD** - Fast voice detection
3. **PyAnnote VAD** - Precise voice refinement
4. **ASR** - Two-step: Transcribe (source) + Translate (target)
5. **Create Clip** - Generate video clip with soft-embedded subtitles

**Why Dual VAD Works Better:**
- **Silero VAD**: Fast initial voice detection
- **PyAnnote VAD**: Precise refinement for overlapping speech
- **Combined**: Handles rapid speaker changes and fast dialogues
- **ASR with Diarization**: Accurate speaker identification

**Supported Languages**: Works with all 96 languages, especially effective for:
- Hindi/Hinglish (code-mixed dialogues)
- Spanish (rapid conversations)
- Japanese (anime with fast exchanges)
- Any content with overlapping or rapid speech

📖 **[Stage Control Reference](docs/WORKFLOW_MODES_GUIDE.md#stage-control)**
</details>

### 🎯 20-40% Better Name Recognition

Advanced bias prompting system for accurate character names:
- **Global Strategy**: Fast, good accuracy
- **Hybrid Strategy**: Best balance ✅ Recommended
- **Chunked Windows**: Maximum accuracy, time-aware

**How it works:**
1. TMDB fetches cast/crew names
2. Pre-NER extracts character mentions  
3. WhisperX uses names as bias during transcription
4. Post-processing corrects any remaining errors

📖 **[Bias Prompting Technical Guide](docs/technical/BIAS_ALL_PHASES_IMPLEMENTATION.md)**

### 📚 Intelligent Glossary System

Context-aware translation preserving cultural terms:
- **1000+ Hinglish Terms**: Pre-loaded master glossary
- **Film-Specific**: Auto-generated from your content
- **ML-Based Selection**: Smart term replacement
- **Adaptive**: Learns from your corrections

**Examples:**
- "didi" → "elder sister" (not "sister")
- "chai" → "chai" (not "tea")
- "namaste" → "namaste" (cultural term preserved)

📖 **[Glossary System Guide](docs/user-guide/GLOSSARY_BUILDER_QUICKSTART.md)**

### ⚙️ Hardware Auto-Configuration

Automatic optimization for your system:
- **GPU Detection**: CUDA (NVIDIA) or MPS (Apple Silicon)
- **Smart Batch Sizing**: Based on available VRAM
- **Model Selection**: Best model for your hardware
- **Performance**: 10-25x faster with GPU vs CPU

**Supports:**
- Apple Silicon (M1/M2/M3) - MPS acceleration
- NVIDIA GPUs - CUDA acceleration
- CPU fallback - Works everywhere

📖 **[Hardware Configuration Guide](docs/HARDWARE_CONFIGURATION_FLOW.md)**

### 🎙️ Professional Audio Processing

- **Speaker Diarization**: Automatic speaker detection and labeling
- **Dual VAD**: Silero (fast) + PyAnnote (precise)
- **Word-Level Alignment**: Perfect subtitle timing
- **Song Detection**: Automatic lyric identification
- **Context-Aware**: Preserves cultural and contextual meaning

### 🎵 Special Features

- **Lyric Detection**: Automatic song identification
- **Character Name Correction**: TMDB metadata integration
- **Resume Capability**: Continue from any interrupted stage
- **Clip Processing**: Test on 5-minute segments before full run
- **Flexible Stage Control**: Enable/disable individual stages

---

## 📖 Documentation

### 🎯 Start Here

| For | Documentation | Time |
|-----|--------------|------|
| **Everyone** | [Documentation Index](docs/INDEX.md) | 2 min browse |
| **New Users** | [Quick Start](docs/QUICKSTART.md) | 10 min setup |
| **International Distributors** | [Multi-Language Guide](docs/WORKFLOW_MODES_GUIDE.md) | 20 min read |
| **Bollywood Creators** | [Glossary Setup](docs/user-guide/GLOSSARY_BUILDER_QUICKSTART.md) | 15 min |
| **System Admins** | [Installation Guide](docs/user-guide/BOOTSTRAP.md) | 30 min |
| **Developers** | [Architecture](docs/ARCHITECTURE.md) | 20 min |

### 📚 Complete Documentation Structure

```
docs/
├── INDEX.md                          # Central navigation hub ⭐
├── QUICKSTART.md                     # 5-minute setup guide
├── WORKFLOW_MODES_GUIDE.md          # Multi-language guide (96 languages)
├── QUICK_REFERENCE_ROOT.md          # Command reference
├── ARCHITECTURE.md                   # System design
│
├── user-guide/
│   ├── BOOTSTRAP.md                  # Installation
│   ├── CONFIGURATION.md              # All settings
│   ├── GLOSSARY_BUILDER_QUICKSTART.md # Hinglish terms
│   └── APPLE_SILICON_QUICK_REF.md   # macOS optimization
│
└── technical/
    └── BIAS_ALL_PHASES_IMPLEMENTATION.md # Bias prompting internals
```

**Quick Links:**
- 📖 [Full Documentation Index](docs/INDEX.md) - Navigate all docs
- ⚡ [Quick Reference](docs/QUICK_REFERENCE_ROOT.md) - Common commands
- 🔧 [Troubleshooting](docs/QUICK_FIX_REFERENCE.md) - Fix common issues
- 🌍 [96 Languages](docs/WORKFLOW_MODES_GUIDE.md#supported-languages) - Language reference

---

## 💻 Installation

### Prerequisites
- Python 3.11+
- 8GB RAM minimum (16GB recommended)
- 10GB disk space minimum (50GB recommended with models)

### Quick Install

```bash
# macOS/Linux
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app
./scripts/bootstrap.sh

# Windows (PowerShell)
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app
.\scripts\bootstrap.ps1
```

### GPU Support

**Apple Silicon (M1/M2/M3):**
```bash
# MPS acceleration enabled automatically
# 10-15x faster than CPU
```

**NVIDIA GPUs:**
```bash
# CUDA acceleration enabled automatically
# 15-25x faster than CPU
```

**CPU-Only:**
```bash
# Works out of the box
# Slower but fully functional
```

📖 **[Detailed Installation Guide](docs/user-guide/BOOTSTRAP.md)**

---

## 🎬 Usage Examples

### Example 1: Default (Hindi → English)
```bash
# Traditional Bollywood workflow
./prepare-job.sh 3-idiots.mp4
./run_pipeline.sh -j <job-id>
# Output: English subtitles with Hindi cultural context preserved
```

### Example 2: Spanish to English
```bash
# International film
./prepare-job.sh la-casa-de-papel.mp4 --transcribe-only -s es
./run_pipeline.sh -j <job-id>

./prepare-job.sh la-casa-de-papel.mp4 --translate-only -s es -t en
./run_pipeline.sh -j <job-id>
```

### Example 3: Japanese to Multiple Languages
```bash
# Anime localization
./prepare-job.sh attack-on-titan-s01e01.mp4 --transcribe-only -s ja
./run_pipeline.sh -j <job-id>

# Generate multiple subtitle tracks
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t en
./run_pipeline.sh -j <job-id>

./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t es
./run_pipeline.sh -j <job-id>

./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t fr
./run_pipeline.sh -j <job-id>
```

### Example 4: Auto-Detect Language
```bash
# Don't know the language? Let Whisper detect it
./prepare-job.sh mystery-movie.mp4 --transcribe-only
./run_pipeline.sh -j <job-id>
```

### Example 5: Quick Test (5-minute clip)
```bash
# Test on a clip before processing full movie
./prepare-job.sh movie.mp4 --start-time 00:10:00 --end-time 00:15:00
./run_pipeline.sh -j <job-id>
```

📖 **[More Examples](docs/WORKFLOW_MODES_GUIDE.md#examples)**

---

## ⚙️ Configuration

### Quick Configuration

The system auto-configures based on your hardware, but you can customize:

```bash
# Enable/disable features
./prepare-job.sh movie.mp4 --disable-diarization  # 50% faster, no speaker labels
./prepare-job.sh movie.mp4 --disable-pyannote-vad # 30% faster

# Workflow modes
./prepare-job.sh movie.mp4 --transcribe-only      # Transcription only
./prepare-job.sh movie.mp4 --translate-only -s es -t en # Translation only

# Language specification
./prepare-job.sh movie.mp4 -s hi -t en            # Hindi to English
./prepare-job.sh movie.mp4 -s ja -t es            # Japanese to Spanish
```

### Advanced Configuration

Edit `config/.env.pipeline` for fine-grained control:

```bash
# Bias prompting
BIAS_ENABLED=true
BIAS_STRATEGY=hybrid         # global, hybrid, or chunked

# Hardware (auto-detected, but can override)
DEVICE=mps                   # mps, cuda, or cpu
BATCH_SIZE=8                 # Auto-optimized for your GPU
WHISPER_MODEL=large-v3       # Auto-selected for your hardware

# Performance
ENABLE_CACHING=true          # API result caching
CHUNK_LENGTH_S=30            # Audio chunk size
```

📖 **[Complete Configuration Guide](docs/user-guide/CONFIGURATION.md)**

---

## 📊 Performance

### Multi-Language Time Savings

| Subtitle Tracks | Traditional | New Workflow | Savings |
|----------------|-------------|--------------|---------|
| 1 track | 100% | 100% | 0% |
| 3 tracks | 300% | 220% | **27%** |
| 5 tracks | 500% | 340% | **32%** |
| 10 tracks | 1000% | 640% | **36%** |

### Name Recognition Accuracy

| Method | Accuracy | Speed | Recommended For |
|--------|----------|-------|-----------------|
| No bias | 60-70% | 1.0x | Not recommended |
| Global | 80-85% | 1.0x | Fast processing |
| **Hybrid** | **85-90%** | **1.0x** | **Production** ✅ |
| Chunked | 90-95% | 1.5-2.0x | Maximum accuracy |

### GPU Acceleration

| Hardware | Speed vs CPU | Recommended Use |
|----------|--------------|-----------------|
| Apple Silicon (M1/M2/M3) | 10-15x | macOS users |
| NVIDIA GPU (6GB+) | 15-25x | Windows/Linux |
| CPU | 1x (baseline) | Fallback |

📖 **[Performance Benchmarks](docs/HARDWARE_CONFIGURATION_FLOW.md)**

---

## 🏗️ Pipeline Architecture

### 15-Stage Production Pipeline

```
Input Video
    ↓
┌───────────────────────────────────────────────────────────┐
│ Audio Processing (Stages 1-5)                            │
│  1. Demux         - Extract audio/video                  │
│  2. TMDB          - Fetch cast/crew metadata            │
│  3. Pre-NER       - Extract character names              │
│  4. Silero VAD    - Voice activity detection (fast)      │
│  5. PyAnnote VAD  - Voice activity detection (precise)   │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Transcription (Stages 6-9)                               │
│  6. WhisperX ASR  - Transcription with character bias ⭐ │
│  7. Song Bias     - Correct song/artist names            │
│  8. Lyrics        - Identify song segments               │
│  9. Bias Correct  - Fix remaining errors                 │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Enhancement (Stages 10-13)                               │
│  10. Diarization  - Speaker identification               │
│  11. Glossary     - Extract Hinglish terms               │
│  12. Second Pass  - Translation refinement ⭐            │
│  13. Post-NER     - Final name correction                │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Output (Stages 14-15)                                    │
│  14. Subtitle Gen - Create SRT with perfect timing       │
│  15. Mux          - Embed subtitles in video             │
└───────────────────────────────────────────────────────────┘
    ↓
Output: Subtitled Video + SRT File
```

**Key Stages (⭐):**
- **Stage 6**: WhisperX with character name bias prompting
- **Stage 12**: Context-aware translation with glossary

📖 **[Detailed Architecture](docs/ARCHITECTURE.md)**

---

## 🎓 Learning Resources

### For New Users
1. **[Quick Start](docs/QUICKSTART.md)** (10 min) - Get running fast
2. **[Quick Reference](docs/QUICK_REFERENCE_ROOT.md)** (5 min) - Common commands
3. **[Workflow Guide](docs/WORKFLOW_MODES_GUIDE.md)** (20 min) - Explore capabilities

### For Bollywood Creators
1. **[Glossary Setup](docs/user-guide/GLOSSARY_BUILDER_QUICKSTART.md)** (15 min)
2. **[Bias Prompting](docs/technical/BIAS_ALL_PHASES_IMPLEMENTATION.md)** (20 min)
3. **[Quality Tips](docs/WORKFLOW_MODES_GUIDE.md#best-practices)** (10 min)

### For International Distributors
1. **[Multi-Language Guide](docs/WORKFLOW_MODES_GUIDE.md)** (20 min)
2. **[96 Languages](docs/WORKFLOW_MODES_GUIDE.md#supported-languages)** (5 min)
3. **[Use Cases](docs/WORKFLOW_MODES_GUIDE.md#real-world-use-cases)** (15 min)

### For Developers
1. **[Architecture](docs/ARCHITECTURE.md)** (20 min)
2. **[Implementation Details](PHASES_2-6_COMPLETE.md)** (30 min)
3. **[API Reference](docs/technical/BIAS_ALL_PHASES_IMPLEMENTATION.md)** (20 min)

📖 **[Complete Documentation Index](docs/INDEX.md)**

---

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><strong>Installation fails</strong></summary>

```bash
# Check Python version (3.11+ required)
python --version

# Clean install
rm -rf .bollyenv
./scripts/bootstrap.sh
```
📖 [Installation Guide](docs/user-guide/BOOTSTRAP.md)
</details>

<details>
<summary><strong>Out of memory errors</strong></summary>

```bash
# Use smaller model
echo "WHISPER_MODEL=base" >> config/.env.pipeline

# Reduce batch size
echo "BATCH_SIZE=1" >> config/.env.pipeline

# Disable diarization (50% memory reduction)
./prepare-job.sh movie.mp4 --disable-diarization
```
📖 [Performance Tuning](docs/HARDWARE_CONFIGURATION_FLOW.md)
</details>

<details>
<summary><strong>Poor name recognition</strong></summary>

```bash
# Enable hybrid bias prompting (recommended)
echo "BIAS_STRATEGY=hybrid" >> config/.env.pipeline

# Verify TMDB metadata
ls out/<job-id>/02_tmdb/

# Check character bias terms
cat out/<job-id>/03_pre_ner/character_bias.txt
```
📖 [Bias Prompting Guide](docs/technical/BIAS_ALL_PHASES_IMPLEMENTATION.md)
</details>

<details>
<summary><strong>translate-only mode fails</strong></summary>

```bash
# Must run transcribe-only first
./prepare-job.sh movie.mp4 --transcribe-only -s es

# Then run translate-only
./prepare-job.sh movie.mp4 --translate-only -s es -t en
```
📖 [Workflow Modes](docs/WORKFLOW_MODES_GUIDE.md#translate-only)
</details>

📖 **[Complete Troubleshooting Guide](docs/QUICK_FIX_REFERENCE.md)**

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Report Issues**: [GitHub Issues](https://github.com/yourusername/cp-whisperx-app/issues)
2. **Suggest Features**: [GitHub Discussions](https://github.com/yourusername/cp-whisperx-app/discussions)
3. **Submit PRs**: Follow our contribution guidelines

### Areas for Contribution
- Additional language support testing
- Glossary term improvements
- Performance optimizations
- Documentation improvements
- Bug fixes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with these amazing open-source projects:

- **[WhisperX](https://github.com/m-bain/whisperX)** - Enhanced Whisper with word-level alignment
- **[OpenAI Whisper](https://github.com/openai/whisper)** - State-of-the-art speech recognition
- **[PyAnnote Audio](https://github.com/pyannote/pyannote-audio)** - Speaker diarization
- **[Silero VAD](https://github.com/snakers4/silero-vad)** - Fast voice activity detection
- **[TMDB](https://www.themoviedb.org/)** - Movie metadata API

---

## 📞 Support

### Documentation
- 📖 [Documentation Index](docs/INDEX.md) - Navigate all docs
- 🚀 [Quick Start](docs/QUICKSTART.md) - Get running fast
- 🌍 [Multi-Language Guide](docs/WORKFLOW_MODES_GUIDE.md) - 96 languages
- ⚡ [Quick Reference](docs/QUICK_REFERENCE_ROOT.md) - Commands
- 🔧 [Troubleshooting](docs/QUICK_FIX_REFERENCE.md) - Fix issues

### Community
- 💬 [GitHub Discussions](https://github.com/yourusername/cp-whisperx-app/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/yourusername/cp-whisperx-app/issues) - Report bugs
- ⭐ Star this repo if you find it useful!

---

## 📈 Project Stats

- **Languages**: 96 supported (ANY-TO-ANY)
- **Pipeline Stages**: 15 (fully configurable)
- **Documentation**: 10,000+ lines
- **Performance**: 27-36% time savings (multi-language)
- **Accuracy**: +20-40% with bias prompting
- **Platforms**: macOS, Windows, Linux

---

## 🗺️ Roadmap

### Current (v2.0)
- ✅ Multi-language support (96 languages)
- ✅ 4 optimized workflow modes
- ✅ Professional documentation
- ✅ Hardware auto-configuration

### Planned
- [ ] Parallel translation jobs
- [ ] Batch processing multiple files
- [ ] Web UI for job management
- [ ] Cloud storage integration
- [ ] Translation quality metrics
- [ ] Auto-detection confidence scores

---

**Quick Links:**  
[📖 Documentation](docs/INDEX.md) | [🚀 Quick Start](docs/QUICKSTART.md) | [🌍 96 Languages](docs/WORKFLOW_MODES_GUIDE.md) | [⚡ Commands](docs/QUICK_REFERENCE_ROOT.md) | [🔧 Troubleshooting](docs/QUICK_FIX_REFERENCE.md)

**Version**: 2.0.0 (Multi-Language Support)  
**Last Updated**: November 14, 2025  
**Status**: Production Ready ✅

---

*Made with ❤️ for international content creators*
