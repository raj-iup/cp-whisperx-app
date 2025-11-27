# Workflow Modes Implementation Plan

## Overview

Add two new workflow modes to `prepare-job.sh/ps1` and `prepare-job.py`:
1. **`--transcribe-only`** - Transcription only in any source language (no translation)
2. **`--translate-only`** - Translation workflow from any source to any target language

**Key Feature:** Support **any-to-any language** pairs (e.g., Hindi→English, Spanish→French, Japanese→German, etc.)

## Current State

### Existing Workflows
1. **`--subtitle-gen`** (default) - Full pipeline (15 stages, Hindi→English optimized)
2. **`--transcribe`** - Basic transcription only (3 stages, minimal)

## New Workflows

### 1. `--transcribe-only` Workflow

**Purpose:** Fast transcription in any source language without translation

**Stages Executed:**
1. ✅ Demux (01) - Extract audio
2. ✅ TMDB (02) - Metadata (for character names, optional)
3. ✅ Pre-NER (03) - Entity extraction (for bias, optional)
4. ✅ Silero VAD (04) - Voice detection
5. ✅ PyAnnote VAD (05) - Voice refinement
6. ✅ ASR (06) - **Transcription in source language**
7. ❌ Song Bias (07) - SKIP
8. ❌ Lyrics Detection (08) - SKIP
9. ❌ Bias Correction (09) - SKIP
10. ❌ Diarization (10) - SKIP
11. ❌ Glossary Builder (11) - SKIP
12. ❌ Second Pass Translation (12) - **SKIP (No translation)**
13. ❌ Post-NER (13) - SKIP
14. ❌ Subtitle Gen (14) - SKIP
15. ❌ Mux (15) - SKIP

**Arguments:**
```bash
--transcribe-only                    # Enable transcribe-only workflow
--source-language CODE               # Source language (e.g., hi, es, ja, fr, de)
                                    # If not specified, auto-detect
```

**Output:**
- `06_asr/segments.json` - Transcript in source language with timestamps
- `06_asr/transcript.txt` - Plain text in source language

**Configuration Overrides:**
```bash
WORKFLOW_MODE=transcribe-only
SOURCE_LANGUAGE=<user-specified>       # e.g., hi, es, ja, fr, de, auto
WHISPER_TASK=transcribe                # Transcribe only (no translate)
SECOND_PASS_ENABLED=false              # Skip translation
LYRIC_DETECT_ENABLED=false
SONG_BIAS_ENABLED=false
BIAS_ENABLED=false
STEP_DIARIZATION=false
POST_NER_ENTITY_CORRECTION=false
POST_NER_TMDB_MATCHING=false
STEP_SUBTITLE_GEN=false
STEP_MUX=false
```

**Use Cases:**
- Quick content review in original language
- Source-only subtitles (no translation)
- Transcription for human translators
- Multi-language content analysis
- Testing/debugging
- Archival/documentation

---

### 2. `--translate-only` Workflow

**Purpose:** Translation from any source language to any target language

**Stages Executed:**
1. ❌ Demux (01) - SKIP (media not needed)
2. ✅ TMDB (02) - Metadata (for glossary, optional)
3. ❌ Pre-NER (03) - SKIP
4. ❌ Silero VAD (04) - SKIP
5. ❌ PyAnnote VAD (05) - SKIP
6. ❌ ASR (06) - **SKIP (assumes segments.json exists)**
7. ✅ Song Bias (07) - Correct song/artist names (optional)
8. ✅ Lyrics Detection (08) - Identify songs (optional)
9. ✅ Bias Correction (09) - Fix errors (optional)
10. ✅ Diarization (10) - OPTIONAL (if speaker labels wanted)
11. ✅ Glossary Builder (11) - Build term dictionary
12. ✅ Second Pass Translation (12) - **Translation to target language**
13. ✅ Post-NER (13) - Name correction
14. ✅ Subtitle Gen (14) - Generate SRT
15. ✅ Mux (15) - OPTIONAL (embed if video available)

**Arguments:**
```bash
--translate-only                     # Enable translate-only workflow
--source-language CODE               # Source language (e.g., hi, es, ja, fr)
--target-language CODE               # Target language (e.g., en, es, fr, de)
```

**Prerequisites:**
- Must have existing transcript: `06_asr/segments.json`
- Created from previous `--transcribe-only` or `--subtitle-gen` run

**Output:**
- `12_second_pass_translation/segments.json` - Translations in target language
- `14_subtitle_gen/subtitles.srt` - SRT file in target language
- `15_mux/<movie>_subtitled.mp4` - Video with subtitles (if video available)

**Configuration Overrides:**
```bash
WORKFLOW_MODE=translate-only
SOURCE_LANGUAGE=<user-specified>      # e.g., hi, es, ja, fr
TARGET_LANGUAGE=<user-specified>      # e.g., en, es, fr, de
SECOND_PASS_ENABLED=true              # Enable translation
LYRIC_DETECT_ENABLED=true             # Optional
SONG_BIAS_ENABLED=true                # Optional
BIAS_ENABLED=true                     # Optional
STEP_SUBTITLE_GEN=true
STEP_MUX=true                         # If video available
# Skip audio processing
STEP_VAD_SILERO=false
STEP_VAD_PYANNOTE=false
STEP_DIARIZATION=false                # Or true if speaker labels wanted
```

**Use Cases:**
- Re-translate with different target language
- Multiple subtitle tracks (e.g., English + Spanish + French from same Hindi)
- Update translation without re-transcribing
- Faster iteration on subtitle quality
- Separate transcription/translation teams
- A/B testing different glossaries

---

## Implementation Plan

### Phase 1: Update `prepare-job.py`

#### 1.1 Add New Workflow Arguments
```python
parser.add_argument(
    "--transcribe-only",
    action="store_true",
    help="Transcription only workflow (no translation)"
)

parser.add_argument(
    "--translate-only",
    action="store_true",
    help="Translation workflow (assumes transcript exists)"
)

parser.add_argument(
    "--source-language",
    "--source-lang",
    dest="source_language",
    default="auto",
    help="Source language code (ISO 639-1: hi, es, ja, fr, de, etc.). Default: auto-detect"
)

parser.add_argument(
    "--target-language",
    "--target-lang",
    dest="target_language",
    default="en",
    help="Target language code for translation (ISO 639-1: en, es, fr, de, etc.). Default: en"
)
```

#### 1.2 Add Workflow Validation
```python
# Validate workflow flags
workflow_flags = [args.transcribe, args.transcribe_only, 
                  args.translate_only, args.subtitle_gen]
if sum(workflow_flags) > 1:
    print("✗ Cannot specify multiple workflow modes")
    sys.exit(1)

# Validate language codes (basic check)
valid_languages = ['auto', 'hi', 'en', 'es', 'fr', 'de', 'ja', 'ko', 'zh', 
                   'ar', 'ru', 'pt', 'it', 'nl', 'pl', 'tr', 'vi', 'id', 'th']
if args.source_language not in valid_languages:
    print(f"⚠ Warning: Source language '{args.source_language}' may not be supported")
if args.target_language not in valid_languages:
    print(f"⚠ Warning: Target language '{args.target_language}' may not be supported")
```

#### 1.3 Determine Workflow Mode and Languages
```python
# Determine workflow mode
if args.transcribe:
    workflow_mode = 'transcribe'
elif args.transcribe_only:
    workflow_mode = 'transcribe-only'
    source_lang = args.source_language
    target_lang = None  # No translation
elif args.translate_only:
    workflow_mode = 'translate-only'
    source_lang = args.source_language
    target_lang = args.target_language
else:
    workflow_mode = 'subtitle-gen'  # default
    source_lang = args.source_language if args.source_language != 'auto' else 'hi'
    target_lang = args.target_language

# Log language settings
logger.info(f"Source language: {source_lang}")
if target_lang:
    logger.info(f"Target language: {target_lang}")
```

#### 1.4 Add Workflow Configurations

In `generate_job_config()` method:

```python
elif workflow_mode == 'transcribe-only':
    if self.logger:
        self.logger.info(f"Workflow: TRANSCRIBE-ONLY ({source_lang} transcription)")
    workflow_config = {
        'WORKFLOW_MODE': 'transcribe-only',
        'SOURCE_LANGUAGE': source_lang,
        'WHISPER_TASK': 'transcribe',
        'SECOND_PASS_ENABLED': 'false',
        'LYRIC_DETECT_ENABLED': 'false',
        'SONG_BIAS_ENABLED': 'false',
        'BIAS_ENABLED': 'false',
        'STEP_DIARIZATION': 'false',
        'POST_NER_ENTITY_CORRECTION': 'false',
        'POST_NER_TMDB_MATCHING': 'false',
        'STEP_SUBTITLE_GEN': 'false',
        'STEP_MUX': 'false'
    }

elif workflow_mode == 'translate-only':
    if self.logger:
        self.logger.info(f"Workflow: TRANSLATE-ONLY ({source_lang} → {target_lang})")
    workflow_config = {
        'WORKFLOW_MODE': 'translate-only',
        'SOURCE_LANGUAGE': source_lang,
        'TARGET_LANGUAGE': target_lang,
        'SECOND_PASS_ENABLED': 'true',
        'LYRIC_DETECT_ENABLED': 'true',
        'SONG_BIAS_ENABLED': 'true',
        'BIAS_ENABLED': 'true',
        'STEP_SUBTITLE_GEN': 'true',
        'STEP_MUX': 'true',
        # Skip audio processing
        'STEP_VAD_SILERO': 'false',
        'STEP_VAD_PYANNOTE': 'false',
        'STEP_DIARIZATION': 'false'
    }
```

### Phase 2: Update `prepare-job.sh`

#### 2.1 Add New Options to Usage
```bash
WORKFLOW MODES:
  --transcribe-hindi   Hindi transcription only (no English translation)
  --translate-english  English translation (assumes Hindi transcript exists)
  --transcribe         Transcribe-only workflow (faster, no subtitles)
  --subtitle-gen       Full subtitle workflow with embedded subtitles (default)
```

#### 2.2 Add Argument Parsing
```bash
--transcribe-hindi)
    WORKFLOW="transcribe-hindi"
    shift
    ;;
--translate-english)
    WORKFLOW="translate-english"
    shift
    ;;
```

#### 2.3 Pass to Python Script
```bash
# Add workflow mode
if [ "$WORKFLOW" = "transcribe-hindi" ]; then
    PYTHON_ARGS+=("--transcribe-hindi")
    log_info "Workflow: TRANSCRIBE-HINDI (Hindi-only)"
elif [ "$WORKFLOW" = "translate-english" ]; then
    PYTHON_ARGS+=("--translate-english")
    log_info "Workflow: TRANSLATE-ENGLISH (translation from Hindi)"
elif [ "$WORKFLOW" = "transcribe" ]; then
    PYTHON_ARGS+=("--transcribe")
    log_info "Workflow: TRANSCRIBE (demux → vad → asr only)"
else
    PYTHON_ARGS+=("--subtitle-gen")
    log_info "Workflow: SUBTITLE-GEN (15 stages, default)"
fi
```

### Phase 3: Update `prepare-job.ps1`

Same changes as `.sh` but in PowerShell syntax:

```powershell
[Parameter(Mandatory=$false)]
[switch]$TranscribeHindi,

[Parameter(Mandatory=$false)]
[switch]$TranslateEnglish,
```

### Phase 4: Update Pipeline Orchestrator

In `scripts/pipeline.py`, add workflow mode detection:

```python
# In get_stages_for_workflow()
def get_stages_for_workflow(self, workflow_mode: str) -> list:
    """Get stages to execute based on workflow mode."""
    
    if workflow_mode == 'transcribe-only':
        return [
            'demux', 'tmdb', 'pre_ner', 
            'silero_vad', 'pyannote_vad', 'asr'
        ]
    
    elif workflow_mode == 'translate-only':
        # Check if ASR output exists
        asr_segments = self.output_dir / "06_asr" / "segments.json"
        if not asr_segments.exists():
            self.logger.error("Source transcript not found!")
            self.logger.error(f"Expected: {asr_segments}")
            self.logger.error("Run with --transcribe-only first")
            raise FileNotFoundError("Missing source transcript")
        
        # Validate source segments have required fields
        import json
        with open(asr_segments, 'r') as f:
            segments_data = json.load(f)
            if 'segments' not in segments_data or not segments_data['segments']:
                raise ValueError("Invalid segments.json: no segments found")
        
        return [
            'tmdb',  # For glossary metadata (optional)
            'song_bias_injection',  # Optional
            'lyrics_detection',     # Optional
            'bias_correction',      # Optional
            'diarization',          # Optional (for speaker labels)
            'glossary_builder',
            'second_pass_translation',  # Core: translation
            'post_ner',
            'subtitle_gen',
            'mux'  # If video available
        ]
    
    elif workflow_mode == 'transcribe':
        # Original transcribe mode
        return ['demux', 'silero_vad', 'asr']
    
    else:  # subtitle-gen (default)
        # All 15 stages
        return self.all_stages
```

### Phase 5: Update Documentation

#### 5.1 README.md
Add workflow modes section with examples

#### 5.2 QUICKSTART.md
Add quick examples for each workflow

#### 5.3 Create WORKFLOW_MODES_GUIDE.md
Comprehensive guide with use cases

---

## Usage Examples

### Example 1: Spanish Transcription Only
```bash
# Transcribe Spanish movie
./prepare-job.sh "/path/to/movie.mp4" --transcribe-only --source-language es
./run_pipeline.sh -j <job-id>

# Output: 06_asr/segments.json (Spanish transcript)
jq -r '.segments[].text' out/<job-dir>/06_asr/segments.json > spanish.txt
```

### Example 2: Japanese to English Translation
```bash
# Step 1: Get Japanese transcript
./prepare-job.sh "/path/to/anime.mp4" --transcribe-only --source-language ja
./run_pipeline.sh -j <job-id-1>

# Step 2: Translate Japanese → English
./prepare-job.sh "/path/to/anime.mp4" --translate-only \
  --source-language ja --target-language en
./run_pipeline.sh -j <job-id-2>

# Output: 14_subtitle_gen/subtitles.srt (English subtitles)
```

### Example 3: Hindi → Multiple Languages
```bash
# Step 1: Get Hindi transcript (once)
./prepare-job.sh "/path/to/movie.mp4" --transcribe-only --source-language hi
./run_pipeline.sh -j <job-id-1>

# Step 2a: Hindi → English
./prepare-job.sh "/path/to/movie.mp4" --translate-only \
  --source-language hi --target-language en
./run_pipeline.sh -j <job-id-2>

# Step 2b: Hindi → Spanish (reuse same transcript)
./prepare-job.sh "/path/to/movie.mp4" --translate-only \
  --source-language hi --target-language es
./run_pipeline.sh -j <job-id-3>

# Step 2c: Hindi → French (reuse same transcript)
./prepare-job.sh "/path/to/movie.mp4" --translate-only \
  --source-language hi --target-language fr
./run_pipeline.sh -j <job-id-4>

# Result: 3 subtitle tracks from 1 transcription!
```

### Example 4: Auto-Detect Language
```bash
# Auto-detect source language
./prepare-job.sh "/path/to/movie.mp4" --transcribe-only
# Whisper will auto-detect: Hindi, Spanish, Japanese, etc.

# Then translate to any target
./prepare-job.sh "/path/to/movie.mp4" --translate-only \
  --source-language auto --target-language en
```

### Example 5: Full Pipeline (Bollywood Default)
```bash
# Default: Hindi → English (optimized for Bollywood)
./prepare-job.sh "/path/to/movie.mp4" --subtitle-gen
./run_pipeline.sh -j <job-id>

# Same as:
./prepare-job.sh "/path/to/movie.mp4" \
  --source-language hi --target-language en
```

### Compare Workflows

| Workflow | Languages | Stages | Time | Output |
|----------|-----------|--------|------|--------|
| `--subtitle-gen` | hi → en | 15 | 100% | English subs + video |
| `--transcribe-only` | any | 6 | 40% | Source transcript |
| `--translate-only` | any → any | 9 | 60% | Target subs from source |
| `--transcribe` | any | 3 | 20% | Raw transcription |

### Supported Language Examples

**Source Languages (Transcription):**
- Hindi (hi), Urdu (ur)
- Spanish (es), French (fr), German (de), Italian (it)
- Japanese (ja), Korean (ko), Chinese (zh)
- Arabic (ar), Turkish (tr), Russian (ru)
- Portuguese (pt), Dutch (nl), Polish (pl)
- Vietnamese (vi), Indonesian (id), Thai (th)
- And 90+ more supported by Whisper

**Target Languages (Translation):**
- Same as above - any combination!

---

## Benefits

### 1. Language Flexibility
- Support for 90+ languages (Whisper-supported)
- Any-to-any language pairs
- Multiple subtitle tracks from one transcription

### 2. Better Workflow
- Separate concerns: transcription vs translation
- Review Hindi accuracy before translating
- Multiple English versions from one Hindi source

### 3. Cost Effective
- Reuse expensive transcription
- Test translation settings quickly
- Share Hindi transcript with translators

### 4. Flexibility
- Hindi-only for Indian audience
- English-only for international
- Both for bilingual content

---

## Migration

### Backward Compatibility
- Existing `--subtitle-gen` unchanged (default)
- Existing `--transcribe` unchanged
- New modes are opt-in

### Existing Jobs
- Old jobs continue to work
- Can run translate-english on old jobs if segments.json exists

---

## Testing Plan

### Test 1: Hindi Transcription
```bash
./prepare-job.sh "test.mp4" --transcribe-hindi
./run_pipeline.sh -j <job-id>
# Verify: 06_asr/segments.json exists with Hindi text
```

### Test 2: English Translation
```bash
# Reuse job from Test 1
./prepare-job.sh "test.mp4" --translate-english
./run_pipeline.sh -j <new-job-id>
# Verify: 14_subtitle_gen/subtitles.srt exists with English
```

### Test 3: Full Workflow (for comparison)
```bash
./prepare-job.sh "test.mp4" --subtitle-gen
./run_pipeline.sh -j <job-id>
# Verify: Same quality as Hindi + English combined
```

---

## Next Steps

1. ✅ Document implementation plan (this file)
2. ⏳ Implement in prepare-job.py
3. ⏳ Implement in prepare-job.sh
4. ⏳ Implement in prepare-job.ps1
5. ⏳ Update pipeline.py orchestrator
6. ⏳ Update documentation
7. ⏳ Test all workflows
8. ⏳ Update README with examples

---

## Files to Modify

### Core Scripts
- `scripts/prepare-job.py` - Add workflow modes
- `prepare-job.sh` - Add argument parsing
- `prepare-job.ps1` - Add argument parsing
- `scripts/pipeline.py` - Add workflow stage logic

### Documentation
- `README.md` - Add workflow examples
- `docs/QUICKSTART.md` - Add quick examples
- `docs/user-guide/CONFIGURATION.md` - Document workflow configs
- Create `docs/WORKFLOW_MODES_GUIDE.md` - Comprehensive guide

### Testing
- Test with sample movie
- Verify each workflow mode
- Check output files
- Measure performance

---

## Summary

This implementation adds two powerful workflow modes that enable:
1. **Faster Hindi-only transcription** (40% of full pipeline time)
2. **Flexible English translation** (reuse Hindi transcript)
3. **Better iteration** (test translations without re-transcribing)
4. **Cleaner separation** (transcription vs translation concerns)

The changes are backward compatible and enable new use cases while maintaining the existing full subtitle generation workflow as the default.
