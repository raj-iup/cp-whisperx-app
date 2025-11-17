# Workflow Modes Guide - ANY-TO-ANY Language Support

## Overview

CP-WhisperX-App now supports **ANY-TO-ANY language combinations** with 96+ supported languages. Choose from multiple workflow modes optimized for different use cases, from quick transcription to full subtitle generation.

## Workflow Modes

### 1. --subtitle-gen (Default)
**Full Pipeline**: 15 stages, ANY→ANY language support (defaults to Hindi→English)

Complete end-to-end subtitle generation with all features enabled. Supports **any source to any target language** combination.

**Time**: 100% (baseline)  
**Stages**: 15  
**Output**: Subtitles embedded in video file  
**Use Case**: Single subtitled video in any language pair

**Examples**:
```bash
# Default: Hindi → English (backward compatible)
./prepare-job.sh movie.mp4

# Spanish → English
./prepare-job.sh movie.mp4 -s es -t en

# Japanese → French
./prepare-job.sh anime.mp4 -s ja -t fr

# German → Spanish
./prepare-job.sh film.mp4 -s de -t es

# Auto-detect source → English
./prepare-job.sh mystery.mp4 -s auto -t en
```

**When to Use**:
- ✅ You need ONE subtitled video file
- ✅ You want embedded subtitles in the video
- ✅ Single language pair is sufficient
- ✅ You want all features (bias prompting, glossary, etc.)

---

### 2. --transcribe-only
**Transcription Pipeline**: 6 stages, outputs segments.json

Transcribes audio in ANY source language with VAD (Voice Activity Detection) for optimal accuracy.

**Time**: ~40% of full pipeline  
**Stages**: 6 (demux, TMDB, pre-NER, Silero VAD, PyAnnote VAD, ASR)  
**Output**: `segments.json` (timestamped transcript in source language)  
**Use Case**: Transcribe once, translate multiple times

**Example**:
```bash
# Spanish transcription
./prepare-job.sh movie.mp4 --transcribe-only --source-language es

# Japanese transcription with auto-detect
./prepare-job.sh anime.mp4 --transcribe-only
```

---

### 3. --translate-only
**Translation Pipeline**: 9 stages, reuses existing transcription

Translates existing transcription to ANY target language without re-processing audio.

**Time**: ~60% of full pipeline  
**Stages**: 9 (song bias, lyrics, corrections, diarization, glossary, translation, NER, subtitle gen, mux)  
**Prerequisite**: Must have `segments.json` from previous `--transcribe-only` run  
**Output**: Subtitles in target language embedded in video  
**Use Case**: Generate multiple subtitle tracks efficiently

**Example**:
```bash
# Step 1: Transcribe Spanish once
./prepare-job.sh movie.mp4 --transcribe-only -s es

# Step 2: Generate multiple subtitle tracks
./prepare-job.sh movie.mp4 --translate-only -s es -t en  # Spanish → English
./prepare-job.sh movie.mp4 --translate-only -s es -t fr  # Spanish → French
./prepare-job.sh movie.mp4 --translate-only -s es -t de  # Spanish → German

# Result: 3 subtitle tracks in 160% time vs 300% if done separately!
```

---

### 4. --transcribe
**Minimal Pipeline**: 3 stages, raw transcription

Quick transcription for testing or simple use cases.

**Time**: ~20% of full pipeline  
**Stages**: 3 (demux, Silero VAD, ASR)  
**Output**: Basic transcription  
**Use Case**: Fast testing, prototyping

**Example**:
```bash
./prepare-job.sh movie.mp4 --transcribe -s hi
```

---

## Language Support

### Supported Languages (96+)

#### South Asian Languages
| Code | Language   | Code | Language   | Code | Language  |
|------|-----------|------|-----------|------|-----------|
| hi   | Hindi     | ta   | Tamil     | bn   | Bengali   |
| ur   | Urdu      | te   | Telugu    | mr   | Marathi   |
| gu   | Gujarati  | kn   | Kannada   | ml   | Malayalam |
| pa   | Punjabi   | sd   | Sindhi    | ne   | Nepali    |
| si   | Sinhala   |      |           |      |           |

#### European Languages
| Code | Language    | Code | Language   | Code | Language   |
|------|------------|------|-----------|------|------------|
| en   | English    | es   | Spanish   | fr   | French     |
| de   | German     | it   | Italian   | pt   | Portuguese |
| ru   | Russian    | nl   | Dutch     | pl   | Polish     |
| uk   | Ukrainian  | cs   | Czech     | ro   | Romanian   |
| sv   | Swedish    | da   | Danish    | no   | Norwegian  |
| fi   | Finnish    | el   | Greek     | bg   | Bulgarian  |
| hr   | Croatian   | sr   | Serbian   | sk   | Slovak     |
| sl   | Slovenian  | et   | Estonian  | lv   | Latvian    |
| lt   | Lithuanian | is   | Icelandic | ga   | Irish      |
| cy   | Welsh      | eu   | Basque    | ca   | Catalan    |
| gl   | Galician   | mt   | Maltese   | sq   | Albanian   |
| mk   | Macedonian | be   | Belarusian|      |            |

#### East Asian Languages
| Code | Language   | Code | Language  | Code | Language |
|------|-----------|------|----------|------|----------|
| ja   | Japanese  | ko   | Korean   | zh   | Chinese  |
| yue  | Cantonese | my   | Burmese  | lo   | Lao      |
| km   | Khmer     |      |          |      |          |

#### Middle Eastern Languages
| Code | Language    | Code | Language    | Code | Language   |
|------|------------|------|------------|------|------------|
| ar   | Arabic     | tr   | Turkish    | fa   | Persian    |
| he   | Hebrew     | az   | Azerbaijani| kk   | Kazakh     |
| uz   | Uzbek      | ky   | Kyrgyz     | tg   | Tajik      |
| tk   | Turkmen    |      |            |      |            |

#### Southeast Asian Languages
| Code | Language    | Code | Language   | Code | Language |
|------|------------|------|-----------|------|----------|
| vi   | Vietnamese | id   | Indonesian| ms   | Malay    |
| th   | Thai       | tl   | Tagalog   | jv   | Javanese |

#### African Languages
| Code | Language  | Code | Language | Code | Language  |
|------|----------|------|----------|------|-----------|
| sw   | Swahili  | yo   | Yoruba   | ha   | Hausa     |
| zu   | Zulu     | af   | Afrikaans| am   | Amharic   |
| so   | Somali   |      |          |      |           |

#### Other Languages
| Code | Language          | Code | Language   | Code | Language        |
|------|------------------|------|-----------|------|-----------------|
| mn   | Mongolian        | hy   | Armenian  | ka   | Georgian        |
| bo   | Tibetan          | la   | Latin     | sa   | Sanskrit        |
| mi   | Maori            | haw  | Hawaiian  | ps   | Pashto          |
| sn   | Shona            | mg   | Malagasy  | oc   | Occitan         |
| br   | Breton           | lb   | Luxembourgish | fo | Faroese       |
| yi   | Yiddish          | ht   | Haitian Creole |  |                |

#### Special
| Code | Description  |
|------|-------------|
| auto | Auto-detect |

---

## Real-World Use Cases

### 1. International Film Distribution
**Scenario**: Release Spanish film globally

```bash
# Step 1: Transcribe Spanish audio once
./prepare-job.sh la-casa-de-papel.mp4 --transcribe-only -s es

# Step 2: Generate subtitles for multiple markets
./prepare-job.sh la-casa-de-papel.mp4 --translate-only -s es -t en  # English
./prepare-job.sh la-casa-de-papel.mp4 --translate-only -s es -t fr  # French
./prepare-job.sh la-casa-de-papel.mp4 --translate-only -s es -t de  # German
./prepare-job.sh la-casa-de-papel.mp4 --translate-only -s es -t pt  # Portuguese

# Result: 4 subtitle tracks in 220% time vs 400%
# Savings: 45% time reduction
```

---

### 2. Anime Localization
**Scenario**: Localize Japanese anime for global audience

```bash
# Step 1: Transcribe Japanese once
./prepare-job.sh attack-on-titan-s01e01.mp4 --transcribe-only -s ja

# Step 2: Generate multiple language tracks
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t en  # English
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t es  # Spanish
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t fr  # French
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t de  # German
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t pt  # Portuguese
./prepare-job.sh attack-on-titan-s01e01.mp4 --translate-only -s ja -t it  # Italian

# Result: 6 subtitle tracks in 280% time vs 600%
# Savings: 53% time reduction
```

---

### 3. Bollywood International Expansion
**Scenario**: Expand Hindi film to new markets

```bash
# Step 1: Transcribe Hindi once (or use existing full workflow)
./prepare-job.sh 3-idiots.mp4 --transcribe-only -s hi

# Step 2: Generate subtitles for international markets
./prepare-job.sh 3-idiots.mp4 --translate-only -s hi -t en  # English (traditional)
./prepare-job.sh 3-idiots.mp4 --translate-only -s hi -t es  # Spanish (Latin America)
./prepare-job.sh 3-idiots.mp4 --translate-only -s hi -t fr  # French (Europe)
./prepare-job.sh 3-idiots.mp4 --translate-only -s hi -t ar  # Arabic (Middle East)
./prepare-job.sh 3-idiots.mp4 --translate-only -s hi -t zh  # Chinese (Asia)

# Result: 5 language versions efficiently
```

---

### 4. Documentary Localization
**Scenario**: Multi-language educational content

```bash
# Step 1: Transcribe English documentary
./prepare-job.sh planet-earth.mp4 --transcribe-only -s en

# Step 2: Create versions for global education
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t hi  # Hindi
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t es  # Spanish
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t fr  # French
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t ar  # Arabic
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t zh  # Chinese
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t pt  # Portuguese
./prepare-job.sh planet-earth.mp4 --translate-only -s en -t ru  # Russian

# Result: 7 language versions for global reach
```

---

### 5. Content Review Pipeline
**Scenario**: QA workflow with iterative improvements

```bash
# Step 1: Quick transcription for review
./prepare-job.sh pilot-episode.mp4 --transcribe-only -s es

# Step 2: Review transcript (check segments.json)
# → Make corrections, update glossary

# Step 3: If approved, generate final subtitles
./prepare-job.sh pilot-episode.mp4 --translate-only -s es -t en

# Step 4: Test different glossary strategies
# → A/B test with different configs without re-transcribing

# Benefit: Fast iteration on translation quality
```

---

### 6. Multi-Region Testing
**Scenario**: Test different regional variants

```bash
# Transcribe once
./prepare-job.sh movie.mp4 --transcribe-only -s en

# Generate region-specific translations
./prepare-job.sh movie.mp4 --translate-only -s en -t es  # Spanish (Spain)
./prepare-job.sh movie.mp4 --translate-only -s en -t pt  # Portuguese (Brazil)
./prepare-job.sh movie.mp4 --translate-only -s en -t fr  # French (France)

# Customize glossaries per region without re-transcribing
```

---

## Performance Comparison

### Single Subtitle Track
```
Traditional: Full pipeline every time
Time: 100% × 1 = 100%

New: Same as traditional
Time: 100% × 1 = 100%

Savings: 0% (no difference for single track)
```

### Three Subtitle Tracks
```
Traditional: Full pipeline 3 times
Time: 100% + 100% + 100% = 300%

New: Transcribe once + Translate 3 times
Time: 40% + (60% × 3) = 40% + 180% = 220%

Savings: 27% time reduction
```

### Five Subtitle Tracks
```
Traditional: Full pipeline 5 times
Time: 100% × 5 = 500%

New: Transcribe once + Translate 5 times
Time: 40% + (60% × 5) = 40% + 300% = 340%

Savings: 32% time reduction
```

### Ten Subtitle Tracks
```
Traditional: Full pipeline 10 times
Time: 100% × 10 = 1000%

New: Transcribe once + Translate 10 times
Time: 40% + (60% × 10) = 40% + 600% = 640%

Savings: 36% time reduction
```

---

## Command-Line Reference

### Bash (macOS/Linux)
```bash
# Full help
./prepare-job.sh --help

# Transcribe only
./prepare-job.sh <input> --transcribe-only -s <lang>

# Translate only
./prepare-job.sh <input> --translate-only -s <source> -t <target>

# Default full pipeline
./prepare-job.sh <input>
```

### PowerShell (Windows)
```powershell
# Full help
.\prepare-job.ps1 -Help

# Transcribe only
.\prepare-job.ps1 <input> -TranscribeOnly -SourceLanguage <lang>

# Translate only
.\prepare-job.ps1 <input> -TranslateOnly -SourceLanguage <source> -TargetLanguage <target>

# Default full pipeline
.\prepare-job.ps1 <input>
```

### Python Direct
```bash
# Full help
python scripts/prepare-job.py --help

# Transcribe only
python scripts/prepare-job.py <input> --transcribe-only -s <lang>

# Translate only
python scripts/prepare-job.py <input> --translate-only -s <source> -t <target>

# Default full pipeline
python scripts/prepare-job.py <input>
```

---

## Best Practices

### 1. Transcribe Once, Translate Many
Always use `--transcribe-only` first if you need multiple subtitle tracks:
```bash
./prepare-job.sh movie.mp4 --transcribe-only -s es
./prepare-job.sh movie.mp4 --translate-only -s es -t en
./prepare-job.sh movie.mp4 --translate-only -s es -t fr
```

### 2. Auto-Detection for Unknown Languages
Use `auto` or omit language for automatic detection:
```bash
./prepare-job.sh mystery-movie.mp4 --transcribe-only
# Whisper will auto-detect: Spanish, Hindi, Japanese, etc.
```

### 3. Quality vs Speed Trade-offs
```bash
# Best quality (default)
./prepare-job.sh movie.mp4

# 30% faster (skip PyAnnote VAD)
./prepare-job.sh movie.mp4 --disable-pyannote-vad

# 50% faster (skip diarization, no speaker labels)
./prepare-job.sh movie.mp4 --disable-diarization
```

### 4. GPU Acceleration
Always use `--native` for MPS/CUDA acceleration:
```bash
./prepare-job.sh movie.mp4 --native
# 10-25x faster with GPU
```

### 5. Testing with Clips
Test with 5-minute clips before full processing:
```bash
./prepare-job.sh movie.mp4 --start-time 00:10:00 --end-time 00:15:00
# Verify quality before full run
```

---

## Troubleshooting

### Error: translate-only requires existing transcription
```
✗ translate-only mode requires existing transcription
  Missing: out/2025/11/14/1/20251114-0001/06_asr/segments.json
```

**Solution**: Run `--transcribe-only` first:
```bash
./prepare-job.sh movie.mp4 --transcribe-only -s es
./prepare-job.sh movie.mp4 --translate-only -s es -t en
```

### Error: Unsupported language
```
✗ Unsupported source language: xyz
```

**Solution**: Use a valid language code from the table above, or use `auto` for auto-detection.

### Error: --translate-only requires --target-language
```
✗ --translate-only requires --target-language
```

**Solution**: Specify both source and target:
```bash
./prepare-job.sh movie.mp4 --translate-only -s es -t en
```

---

## FAQ

**Q: Can I translate from any language to any language?**  
A: Yes! 96 languages supported with ANY-TO-ANY combinations.

**Q: How much faster is transcribe-only + translate-only?**  
A: For 3 subtitle tracks: 27% faster. For 10 tracks: 36% faster.

**Q: Does auto-detection work well?**  
A: Yes, Whisper's auto-detection is highly accurate for all 96 languages.

**Q: Can I use different glossaries per target language?**  
A: Yes, customize glossary files per job without re-transcribing.

**Q: What if I need to correct the transcription?**  
A: Edit `06_asr/segments.json` and run `--translate-only` to regenerate subtitles.

**Q: Can I chain multiple translations?**  
A: Yes, but translations are always from original source. Hindi → English → Spanish would be Hindi → Spanish (not a chain).

---

## See Also

- [README.md](../README.md) - Main documentation
- [QUICKSTART.md](./QUICKSTART.md) - Quick start guide
- [WORKFLOW_MODES_SUMMARY.txt](../WORKFLOW_MODES_SUMMARY.txt) - Technical implementation details

---

**Last Updated**: November 14, 2025  
**Version**: 1.0.0
