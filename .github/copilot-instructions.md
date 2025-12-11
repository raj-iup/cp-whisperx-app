# Copilot Instructions — CP-WhisperX-App

**Version:** 7.2 (BRD-PRD-TRD Framework) | **Status:** 🎊 **100% PERFECT COMPLIANCE** 🎊 | **Pre-commit Hook:** ✅ Active

**🚨 NEW: § 21 BRD-PRD-TRD Framework (2025-12-09):**
- 📋 **MANDATORY**: BRD-PRD-TRD for new features (>200 LOC)
- 📝 **PRD First**: User stories with acceptance criteria before code
- 🔗 **Traceability**: Every feature traces to BRD (business need)
- ✅ **Examples**: 3 complete PRDs available in docs/requirements/prd/
- 📚 **See**: DEVELOPER_STANDARDS.md § 21 for complete guidance

**🚨 CRITICAL: AD-009 Development Philosophy (2025-12-05):**
- 🎯 **OPTIMIZE FOR QUALITY**: Highest accuracy output is the ONLY goal
- 🔥 **NO BACKWARD COMPATIBILITY**: We're in active development (pre-v3.0)
- ⚡ **AGGRESSIVE OPTIMIZATION**: Replace suboptimal code, don't wrap it
- 🧪 **TEST QUALITY METRICS**: ASR WER, Translation BLEU, Subtitle Quality
- ❌ **NO COMPATIBILITY LAYERS**: Remove old code, implement optimal solution
- ✅ **DIRECT EXTRACTION**: Don't delegate to old implementations during refactoring

**Major Updates in v7.1 (2025-12-06 15:20 UTC):**
- 🏛️ **AD-010 ADDED**: Workflow-specific output requirements
- 📋 **M-001 Complete**: Monthly alignment audit (95% → 100% coverage)
- ✅ **All 10 ADs**: Documented across all 4 documentation layers
- 📝 **Workflow Updates**: Added AD-010 references to § 1.5 (transcribe, translate, subtitle)

**Major Updates in v7.0 (2025-12-05 14:32 UTC):**
- 🎯 **AD-009**: Quality-first development philosophy (CRITICAL - read first)
- 🔥 **Development Mindset**: "Build optimal solution" not "preserve old code"
- ⚡ **Refactoring Approach**: Direct extraction + optimization, not wrappers
- 📋 **See**: AD-009_DEVELOPMENT_PHILOSOPHY.md for complete guidance

**Major Updates in v6.6 (AD-007 Import Consistency):**
- 🏛️ **AD-007 MANDATORY**: Consistent shared/ import paths
- 🐛 **Bug #4 Fixed**: Bias window generator import (whisperx_integration.py:1511)
- 📝 **Import Rule**: ALL shared/ imports must use "shared." prefix
- ✅ **Lazy Imports**: Same rule applies to try/except imports
- 📋 **Pattern**: from shared.module import function (always)

**Major Updates in v6.5 (AD-006 Configuration Priority):**
- 🏛️ **AD-006 MANDATORY**: Job-specific parameters override system defaults
- 📋 **Configuration Pattern**: 4-tier priority hierarchy (job.json → job env → system config → code defaults)
- ✅ **All Stages**: Must read job.json before using system config
- 🐛 **Bug #3 Fixed**: Language detection now reads from job.json
- 📝 **Standard Pattern**: Documented mandatory implementation pattern

**Major Updates in v6.2 (2025-12-03):**
- 🐛 **Syntax Error Fixed**: Duplicate exc_info=True parameters (8 instances)
- 🐛 **Error Handling Guide**: Added common mistake warning
- 📝 **Best Practice**: Always use exc_info=True exactly once

**Major Updates in v6.1 (2025-12-03):**
- 🐛 **Source Language Optional**: Transcribe workflow auto-detects language
- 🐛 **TMDB Workflow-Aware**: Only enabled for subtitle workflow (movies/TV)
- 🐛 **StageManifest Enhanced**: Added add_intermediate() method
- 🐛 **Script Path Fixed**: Corrected TMDB script reference

**Major Updates in v6.0:**
- 🆕 **Automated Model Updates**: Weekly checks for new AI model releases
- 🆕 **Optimal Routing**: Data-driven model selection from AI_MODEL_ROUTING.md
- 🆕 **Cost Optimization**: Track and optimize AI usage costs
- 🆕 **Auto-Sync**: GitHub Actions keeps routing decisions current

---

## ⚡ Before You Respond

**🔥 AD-009 CRITICAL CHECKS (NEW - Check FIRST):**
1. **Am I optimizing for QUALITY (accuracy/performance)?** (AD-009) 🎯
2. **Am I removing old code or wrapping it?** (Remove = good, Wrap = bad) 🔥
3. **Is this the OPTIMAL implementation?** (If no, improve it) ⚡
4. **Am I preserving compatibility with internal code?** (DON'T - only external APIs) ❌

**Standard Compliance Checks:**
5. Will I use `logger` instead of `print()`? (§ 2.3)
6. Are imports organized Standard/Third-party/Local? (§ 6.1)
7. **Are shared/ imports using "shared." prefix? (§ 6.1 - AD-007)** ⭐
8. If stage: Does it use StageIO with `enable_manifest=True`? (§ 2.6)
9. Are outputs going to `io.stage_dir` only? (§ 1.1)
10. Am I using `load_config()` not `os.getenv()`? (§ 4.2)
11. **Am I reading job.json BEFORE using system config? (§ 4 - AD-006)**
12. **Cross-platform compatible? (Use `pathlib`, not hardcoded paths)** (§ 1.2)
13. **If subprocess with files: Did I validate path + use Path.resolve()? (AD-011)** ⭐
14. **If subprocess with files: Did I use str(path) for command args? (AD-011)** ⭐
15. **If creating log files: Am I using logs/ directory? (AD-012)** 🆕 ⭐
16. **If creating log files: Am I using get_log_path() helper? (AD-012)** 🆕 ⭐
17. **If creating test files: Am I using tests/ directory? (AD-013)** 🆕 ⭐
18. **If creating test files: Is it in the correct category? (unit/integration/functional/manual)** 🆕 ⭐
19. **If creating shell script: Do I need Windows (.ps1) equivalent?** (§ 1.2)
20. **If creating stage script: Is it named `{NN}_{stage_name}.py`?** (File Naming)
21. **If testing: Am I using standard test media samples?** (§ 1.4)
22. **If workflow: Am I following context-aware patterns?** (§ 1.5)
23. **If subtitle workflow: Am I checking for baseline/glossary/cache first? (AD-014)** 🆕 ⭐
24. **If subtitle workflow: Am I computing media_id for caching? (AD-014)** 🆕 ⭐
25. **Error handling: Am I using exc_info=True exactly once?** (§ 5)
26. **ASR/Transcription: Am I using hybrid MLX architecture?** (§ 2.7)
27. **If new feature (>200 LOC): Does BRD-PRD-TRD exist? (DEVELOPER_STANDARDS.md § 21)** 🆕 ⭐
28. **If architectural change: Is AD documented in ARCHITECTURE.md?** 🆕 ⭐

**If NO to any → Check the relevant § section below**

---

## 🏛️ Architectural Decisions Quick Reference (NEW) 🆕

**Authoritative Source:** ARCHITECTURE.md  
**Developer Guide:** DEVELOPER_STANDARDS.md § 20

**All 14 Approved Architectural Decisions:** 🆕

- **AD-001:** 12-stage architecture (optimal, no major refactoring) ✅
- **AD-002:** ASR modularization (use `whisperx_module/`, not monolith) ✅
- **AD-003:** Translation single-stage (defer 4-stage split) ✅
- **AD-004:** 8 virtual environments (no new venvs needed) ✅
- **AD-005:** Hybrid MLX backend (8-9x faster with subprocess isolation) ✅
- **AD-006:** Job-specific parameters MANDATORY (read job.json first) ✅
- **AD-007:** Consistent shared/ imports (always use "shared." prefix) ✅
- **AD-008:** Hybrid alignment architecture (subprocess prevents segfaults) ✅
- **AD-009:** Quality over compatibility (optimize aggressively) ✅
- **AD-010:** Workflow-specific outputs (transcribe → txt, translate → txt, subtitle → srt/vtt) ✅
- **AD-011:** Robust file path handling (pathlib + pre-flight validation for subprocess) 🔄
- **AD-012:** Centralized log management (all logs in logs/ directory) 🆕 ⏳
- **AD-013:** Organized test structure (all tests categorized in tests/ directory) 🆕 ⏳
- **AD-014:** Multi-phase subtitle workflow (reuse baseline/glossary/cache for quality) 🆕 ⏳

**Quick Patterns:**

```python
# Per AD-002: Use ASR modules
from whisperx_module.transcription import TranscriptionEngine
from whisperx_module.alignment import AlignmentEngine

# Per AD-004: Use correct venv (in shebang)
#!/path/to/venv/whisperx/bin/python  # Stage 06

# Per AD-005 + AD-008: Hybrid MLX
backend = create_backend("auto")  # Auto-selects MLX on Apple Silicon
# Alignment automatically uses subprocess with MLX

# Per AD-006: Read job.json first
config = load_config()  # System defaults
job_data = json.load(open(job_dir / "job.json"))  # Override
param = job_data.get('key', config.get('key', default))

# Per AD-007: Shared imports
from shared.module import function  # ✅ Correct
# NOT: from module import function  # ❌ Wrong

# Per AD-010: Workflow-specific outputs
if workflow == "transcribe":
    # Skip subtitle generation, export transcript only
    stages = stages[:7]  # Stop at alignment
elif workflow == "translate":
    # Skip subtitle generation, export translated transcript
    stages = stages[:7] + ["10_translation"]
else:  # subtitle workflow
    # Generate all subtitle tracks
    stages = stages  # Full pipeline

# Per AD-011: File path validation (NEW) 🆕
from pathlib import Path

# Always use absolute paths
input_file = Path(file_path).resolve()

# Pre-flight validation BEFORE subprocess
if not input_file.exists():
    logger.error(f"❌ Input file not found: {input_file}")
    return False

if not input_file.is_file():
    logger.error(f"❌ Not a file: {input_file}")
    return False

if input_file.stat().st_size == 0:
    logger.error(f"❌ File is empty: {input_file}")
    return False

# Test accessibility
try:
    with open(input_file, 'rb') as f:
        f.read(1)
except PermissionError:
    logger.error(f"❌ Permission denied: {input_file}")
    return False

# Build subprocess command with proper string conversion
cmd = ['ffmpeg', '-i', str(input_file), str(output_file)]  # str() handles special chars

# Enhanced FFmpeg error handling
try:
    subprocess.run(cmd, capture_output=True, text=True, check=True)
except subprocess.CalledProcessError as e:
    if e.returncode == 234:
        logger.error("❌ FFmpeg error 234: Invalid input/output")
        logger.error("   Possible: special chars, corruption, format")
    # Parse stderr for actionable messages...

# Per AD-012: Log file placement (NEW) 🆕
from shared.log_paths import get_log_path

# Get log path for test/debug
log_file = get_log_path("testing", "transcribe", "mlx")
# Returns: logs/testing/manual/20251208_103045_transcribe_mlx.log

# Use in script
with open(log_file, 'w') as f:
    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

# ❌ NEVER write logs to project root
# with open("test.log", "w") as f:  # WRONG!

# Per AD-013: Test file placement (NEW) 🆕
# ❌ NEVER create test files in project root
# test-my-feature.sh  # WRONG!
# test_my_feature.py  # WRONG!

# ✅ ALWAYS place in appropriate tests/ category
tests/unit/test_my_feature.py           # Unit test
tests/integration/test_my_integration.py # Integration test
tests/functional/test_my_workflow.py     # Functional/E2E test
tests/manual/feature/test-script.sh      # Manual script

# Per AD-014: Multi-phase subtitle workflow (NEW) 🆕
from shared.media_identity import compute_media_id
from shared.cache_manager import MediaCacheManager

# Compute media ID for caching
media_id = compute_media_id(Path("movie.mp4"))

# Check for cached baseline
cache_mgr = MediaCacheManager()
if cache_mgr.has_baseline(media_id):
    baseline = cache_mgr.get_baseline(media_id)
    logger.info("✅ Reusing baseline from previous run")
else:
    baseline = run_baseline_generation(...)
    cache_mgr.store_baseline(media_id, baseline)

# ❌ NEVER skip baseline check on subtitle workflow
# ❌ NEVER recompute ASR/alignment if baseline exists
```

---

## 📍 Standard Test Media (ALWAYS USE THESE)

**Sample 1: English Technical**
- File: `in/Energy Demand in AI.mp4`
- Use for: Transcribe, Translate workflows
- Quality target: ASR WER ≤5%, Translation BLEU ≥90%

**Sample 2: Hinglish Bollywood**
- File: `in/test_clips/jaane_tu_test_clip.mp4`
- Use for: Subtitle, Transcribe, Translate workflows
- Quality target: ASR WER ≤15%, Subtitle Quality ≥88%

**See:** § 1.4 for complete test media documentation

---

## 🎯 Core Workflows (Context-Aware)

**1. Subtitle Workflow** (§ 1.5)
- Input: Bollywood/Indic media (movies/TV shows)
- Output: Multiple soft-embedded subtitle tracks (hi, en, gu, ta, es, ru, zh, ar)
- Features: Character names, cultural terms, speaker diarization, temporal coherence
- **TMDB:** ✅ Enabled (fetches cast, crew, character names)

**2. Transcribe Workflow** (§ 1.5)
- Input: Any media (YouTube, podcasts, lectures, general content)
- Output: Transcript in SAME language as source
- Features: Domain terminology, proper nouns, native script output
- **Source Language:** Optional (auto-detects if not specified)
- **TMDB:** ❌ Disabled (not needed for non-movie content)

**3. Translate Workflow** (§ 1.5)
- Input: Any media (YouTube, podcasts, lectures, general content)
- Output: Transcript in SPECIFIED target language
- Features: Cultural adaptation, glossary terms, formality preservation
- **Source Language:** Required (must be Indian language for IndicTrans2)
- **TMDB:** ❌ Disabled (not needed for non-movie content)

---

## 📍 Model Routing (AUTO-UPDATED)

**Primary Source:** `docs/AI_MODEL_ROUTING.md` (auto-updates weekly)

**Quick Routing Principle:**
- Start with cheapest model that can do the task correctly
- Escalate only if: complexity increases, multi-file changes, high-risk territory, or stuck after 2 attempts

**Escalation Ladder:**
1. GPT-4 Turbo (default, small edits)
2. GPT-4o (fast iteration)  
3. Claude 3.5 Sonnet (refactoring, standards compliance)
4. o1 (deep reasoning, architecture)

**Task Types:**
- T1: Read/Explain → GPT-4 Turbo
- T2: Small change (≤1 file, ≤50 LOC) → GPT-4o
- T3: Medium change (2-5 files) → Claude 3.5 Sonnet
- T4: Large change (≥6 files) → o1 (high risk)
- T5: Debug/Investigate → GPT-4 Turbo → o1 (complex)
- T6: Docs/Comms → GPT-4 Turbo
- T7: Standards compliance → Claude 3.5 Sonnet

**Risk Levels:**
- Low: No stage boundaries, manifests, or CI
- Medium: Touches stage logic or multiple files
- High: Manifests, resume logic, CI, dependencies, >10 files

**Cost Monitoring:** Track usage with `./tools/model-usage-stats.py`

**See:** AI_MODEL_ROUTING.md § 3 for complete routing table (updated weekly)

**Last Synced:** 2025-12-03 (auto-synced by GitHub Actions)

---

## § 1.4 Standard Test Media (ALWAYS USE THESE)

**Purpose:** Establish reproducible testing baseline with diverse use cases.

### Sample 1: English Technical Content
**File:** `in/Energy Demand in AI.mp4`  
**Size:** ~14 MB | **Duration:** 2-5 minutes  
**Language:** English | **Type:** Technical/Educational  
**Use For:** Transcribe, Translate workflows

**Characteristics:**
- Clear English audio with technical terminology (AI, energy, demand)
- Minimal background noise
- Good for testing ASR accuracy on technical content
- Ideal for English-to-Indic translation testing

**Quality Targets:**
- ASR Accuracy: ≥95% WER
- Translation BLEU: ≥90%
- Processing Time: <3 minutes

### Sample 2: Hinglish Bollywood Content
**File:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Size:** ~28 MB | **Duration:** 1-3 minutes  
**Language:** Hindi/Hinglish (mixed) | **Type:** Entertainment  
**Use For:** Subtitle, Transcribe, Translate workflows

**Characteristics:**
- Mixed Hindi-English (Hinglish) dialogue
- Bollywood dialogue patterns, emotional/casual speech
- Background music possible, multiple speakers
- Real-world subtitle generation challenge

**Quality Targets:**
- ASR Accuracy: ≥85% WER
- Subtitle Quality: ≥88%
- Context Awareness: ≥80%
- Glossary Application: 100%

**See:** `docs/user-guide/workflows.md` for detailed test scenarios

---

## § 1.5 Core Workflows (Context-Aware)

### 1. Subtitle Workflow
**Purpose:** Generate context-aware multilingual subtitles for Bollywood/Indic media

**Input:** Indic/Hinglish movie media source  
**Output:** Original media + soft-embedded subtitle tracks (hi, en, gu, ta, es, ru, zh, ar) **(per AD-010)**  
**Output Location:** `out/{date}/{user}/{job}/12_mux/`

**Pipeline:** demux → tmdb ✅ → glossary_load → source_sep → pyannote_vad → whisperx_asr → alignment → translate → subtitle_gen → mux **(full 12-stage pipeline)**

**Context-Aware Features:**
- Character names preserved via glossary
- Cultural terms (Hindi idioms, relationship terms)
- Tone adaptation (formal vs. casual)
- Temporal coherence (consistent terminology)
- Speaker attribution (diarization)
- **Lyrics detection (Stage 08) - MANDATORY**
  - Identifies song/music segments
  - Prevents literal translation of lyrics
  - Preserves cultural significance
- **Hallucination removal (Stage 09) - MANDATORY**
  - Removes ASR artifacts ("Thanks for watching", repeated phrases)
  - Cleans background music-induced errors
  - Ensures 88%+ subtitle quality

**Example:**
```bash
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar
```

### 2. Transcribe Workflow
**Purpose:** Create high-accuracy transcript in SOURCE language

**Input:** Any media source (YouTube, podcasts, lectures, general content)
**Output:** Text transcript in SAME language as source **(per AD-010 - NO subtitles)**  
**Output Location:** `out/{date}/{user}/{job}/07_alignment/transcript.txt`

**Pipeline:** demux → glossary_load → source_sep (optional) → pyannote_vad → whisperx_asr → alignment **(stops at stage 07)**

**TMDB:** ❌ **Disabled** (not needed for non-movie content)

**Context-Aware Features:**
- Domain terminology preserved
- Proper nouns (names, places, organizations)
- Language-specific output (native script for Hindi)
- Context-aware punctuation
- Capitalization (proper noun detection for English)
- **Auto-detects language if not specified**

**Example:**
```bash
# Auto-detect language (NEW in v6.1)
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe

# Explicit English
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe -s en

# Hindi content
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow transcribe -s hi
```

### 3. Translate Workflow
**Purpose:** Create high-accuracy transcript in TARGET language

**Input:** Indian language media (IndicTrans2 constraint)
**Output:** Text transcript in SPECIFIED target language **(per AD-010 - NO subtitles)**  
**Output Location:** `out/{date}/{user}/{job}/10_translation/transcript_{target_lang}.txt`

**Pipeline:** demux → glossary_load → source_sep (optional) → pyannote_vad → whisperx_asr → alignment → translate **(stops at stage 10)**

**TMDB:** ❌ **Disabled** (not needed for non-movie content)

**Context-Aware Features:**
- Cultural adaptation (idioms, metaphors localized)
- Formality levels maintained
- Named entities transliterated appropriately
- Glossary terms preserved
- Temporal consistency (same term translated consistently)
- Numeric/date formats localized

**Translation Routing:**
- Indic languages: IndicTrans2 (highest quality)
- Non-Indic: NLLB-200 (broad support)
- Fallback: Hybrid approach

**Language Constraint (NEW in v6.1):**
- ✅ Source language **MUST** be Indian language (hi, ta, te, etc.)
- ✅ Target language can be ANY language
- ❌ English→Hindi NOT supported (use transcribe instead)

**Example:**
```bash
# Hindi → English (WORKS)
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow translate -s hi -t en

# Hindi → Spanish (WORKS)
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow translate -s hi -t es

# English → Hindi (FAILS - use transcribe instead)
# ./prepare-job.sh --media file.mp4 --workflow translate -s en -t hi  ❌
```
# Hindi → English
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow translate \
  --source-language hi --target-language en

# Hindi → Spanish
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow translate \
  --source-language hi --target-language es
```

**See:** `docs/user-guide/workflows.md` for complete workflow documentation

---

## § 1.6 Caching & ML Optimization

**Purpose:** Enable subsequent workflows with similar media to perform optimally over time.

### Intelligent Caching Layers

**1. Model Cache (Shared)**
- Location: `{cache_dir}/models/`
- Stores: Downloaded model weights (WhisperX, IndicTrans2, PyAnnote)
- Benefits: Avoid re-downloading 1-5 GB per run

**2. Audio Fingerprint Cache**
- Location: `{cache_dir}/fingerprints/`
- Stores: Audio characteristics, detected language, noise profile
- Benefits: Skip demux/analysis for identical media

**3. ASR Results Cache (Quality-Aware)**
- Location: `{cache_dir}/asr/`
- Cache Key: `SHA256(audio_content + model_version + language + config_params)`
- Benefits: Reuse ASR results for same audio (saves 2-10 minutes)
- Invalidation: Model version change, config parameter change, or `--no-cache` flag

**4. Translation Cache (Contextual)**
- Location: `{cache_dir}/translations/`
- Context-Aware Matching: Exact segment (100% reuse), similar segment >80% (reuse with adjustment)
- Benefits: Reuse translations for similar content (saves 1-5 minutes)

**5. Glossary Learning Cache**
- Location: `{cache_dir}/glossary_learned/`
- Stores: Per-movie learned terms, character names, cultural terms, frequency analysis
- Benefits: Improve accuracy on subsequent processing of same movie/genre

### ML-Based Optimization

**1. Adaptive Quality Prediction**
- ML Model: Lightweight XGBoost classifier
- Predicts: Optimal Whisper model size, source separation needed, expected ASR confidence
- Benefits: 30% faster processing on clean audio (use smaller model)

**2. Context Learning from History**
- Character name recognition from previous jobs
- Cultural term patterns learning
- Translation memory from approved translations
- Benefits: Consistent terminology, higher accuracy over time

**3. Similarity-Based Optimization**
- Detects similar media via audio fingerprinting
- Reuses processing decisions, glossaries, model selection
- Benefits: 40-95% time reduction on similar content

### Cache Configuration

**In config/.env.pipeline:**
```bash
# Caching Configuration
ENABLE_CACHING=true                          # Master switch
CACHE_DIR=~/.cp-whisperx/cache              # Cache location
CACHE_MAX_SIZE_GB=50                        # Total cache size limit
CACHE_ASR_RESULTS=true                      # Cache ASR outputs
CACHE_TRANSLATIONS=true                     # Cache translations
CACHE_AUDIO_FINGERPRINTS=true              # Cache audio analysis
CACHE_TTL_DAYS=90                          # Cache expiration (days)

# ML Optimization
ENABLE_ML_OPTIMIZATION=true                 # Enable ML predictions
ML_MODEL_SELECTION=adaptive                 # adaptive|fixed
ML_QUALITY_PREDICTION=true                  # Predict optimal settings
ML_LEARNING_FROM_HISTORY=true              # Learn from past jobs
```

### Cache Management

```bash
# View cache statistics
./tools/cache-manager.sh --stats

# Clear specific cache type
./tools/cache-manager.sh --clear asr

# Disable caching for one job
./prepare-job.sh --media in/file.mp4 --no-cache
```

### Expected Performance Improvements

| Scenario | First Run | Subsequent Run | Improvement |
|----------|-----------|----------------|-------------|
| Identical media | 10 min | 30 sec | 95% faster |
| Same movie, different cut | 10 min | 6 min | 40% faster |
| Similar Bollywood movie | 10 min | 8 min | 20% faster |

**See:** `docs/technical/caching-ml-optimization.md` for complete caching architecture

---

## § 2.7 MLX Backend Architecture (NEW in v6.7)

**Hybrid MLX Architecture for Apple Silicon (AD-005 + AD-008)** 🆕

**Architectural Decisions:**
- **AD-005:** Hybrid MLX backend for optimal performance
- **AD-008:** Subprocess isolation prevents segfaults
- **Reference:** ARCHITECTURE_ALIGNMENT_2025-12-04.md

### When to Use MLX Backend

✅ **Use MLX when (per AD-005):**
- Running on Apple Silicon (M1/M2/M3/M4)
- Need maximum performance (8-9x faster than CPU)
- Transcription or subtitle workflows
- Have MPS device available

❌ **Don't use MLX when:**
- Running on non-Apple hardware
- Only CPU or CUDA available
- System stability more important than speed

### Architecture Overview

**Hybrid Design:**
```python
# Step 1: Transcription (MLX - Fast)
backend = create_backend("mlx", model="large-v3", device="mps", ...)
result = backend.transcribe(audio_file, language="en")
# Duration: ~84 seconds for 12min audio (8-9x faster!)

# Step 2: Alignment (WhisperX Subprocess - Stable)
aligned = processor.align_segments(result, audio_file, "en")
# Automatically uses subprocess when backend is MLX
# Duration: ~39 seconds
# Prevents segfaults through process isolation
```

### Key Implementation Patterns

**1. MLX Backend Setup:**
```python
from whisper_backends import create_backend

# System automatically selects MLX on Apple Silicon
backend = create_backend(
    backend_type="mlx",  # or "auto"
    model_name="large-v3",
    device="mps",
    compute_type="float16",
    logger=logger
)
```

**2. Alignment Delegation:**
```python
# whisperx_integration.py handles this automatically

def align_segments(self, result, audio_file, language):
    """Hybrid alignment dispatcher"""
    if self.backend.name == "mlx-whisper":
        # Use WhisperX subprocess (prevents segfault)
        return self.align_with_whisperx_subprocess(
            result["segments"], audio_file, language
        )
    else:
        # Use backend's native alignment
        return self.backend.align_segments(...)
```

**3. Configuration:**
```bash
# config/.env.pipeline
WHISPER_BACKEND=mlx              # Primary ASR backend
ALIGNMENT_BACKEND=whisperx        # Alignment in subprocess
```

### Critical Rules

**✅ DO:**
- Let the system handle MLX → WhisperX alignment automatically
- Use subprocess for any MLX alignment needs
- Set 5-minute timeout for alignment subprocess
- Handle subprocess failures gracefully (fallback to segments without words)

**❌ DON'T:**
- Call `backend.align_segments()` directly on MLX backend
- Run MLX `transcribe()` twice in same process
- Try to align in-process with MLX (causes segfault)
- Modify the hybrid architecture unless necessary

### Performance Expectations

**Test Results (12.4 min audio):**
- Transcription: 84 seconds (8-9x faster than CPU)
- Alignment: 39 seconds (subprocess)
- Total: 123 seconds (2 minutes)
- Output: 200 segments with word-level timestamps
- Stability: 100% (no segfaults)

**vs CTranslate2/CPU:**
- Status: Crashed after 11 minutes
- Performance: N/A (never completed)
- Stability: 0%

### Troubleshooting

**If MLX transcription fails:**
```python
# System falls back to WhisperX automatically
# Check logs for: "Signaling fallback to WhisperX backend..."
```

**If alignment subprocess fails:**
```python
# Returns segments without word timestamps
# Check logs for: "Alignment subprocess failed (exit code N)"
```

**If seeing segfaults:**
```python
# Check ALIGNMENT_BACKEND setting
# Should be "whisperx", not "mlx" or "same"
```

---

## 🚧 Implementation Status

**Current Architecture:** v2.0 (Simplified 3-6 Stage Pipeline)  
**Target Architecture:** v3.0 (Context-Aware Modular 12-Stage Pipeline)  
**Migration Progress:** 95% Documentation Complete (Phase 4)

### What Works Now (v2.0) ✅

**Use These Patterns:**
- ✅ Configuration loading (100% compliant) - `load_config()`
- ✅ Logging system (100% compliant) - `logger.info()` not `print()`
- ✅ Multi-environment support - MLX/CUDA/CPU
- ✅ Error handling patterns - Try/except with logging
- ✅ Type hints and docstrings (100% compliant)
- ✅ Standard test media - Two samples defined (§ 1.4)
- ✅ Core workflows documented - Subtitle/Transcribe/Translate (§ 1.5)
- ✅ **Hybrid MLX Architecture** - 8-9x faster ASR (§ 2.7) 🆕
- ✅ **Subprocess Alignment** - Prevents MLX segfaults (§ 2.7) 🆕

**Partially Implemented:**
- ✅ Stage module pattern (100% adoption) - ALL stages use StageIO ✅
- ✅ Manifest tracking (100% adoption) - All stages track inputs/outputs ✅
- ✅ Stage isolation (100% adoption) - Stage-based directories enforced ✅
- ✅ Context-aware processing (90% adoption) - Implemented in subtitle workflow ✅
- ⏳ Intelligent caching (0% adoption) - Planned in Phase 5 (§ 1.6) 🆕

### What's Coming (v3.0) ⏳

**In Active Development:**
- ⏳ Full 12-stage modular pipeline
- ✅ Universal StageIO adoption (100% achieved)
- ✅ Complete manifest tracking (100% achieved)
- ⏳ Stage-level testing infrastructure
- ⏳ Stage enable/disable per job
- ⏳ Advanced features (retry, caching, circuit breakers)

**See:** [Implementation Status Dashboard](../docs/IMPLEMENTATION_STATUS.md) for current progress.

### Code Generation Guidelines

**When generating NEW stage code:**
1. ✅ **Follow DEVELOPER_STANDARDS.md patterns** (even if not widely adopted yet)
2. ✅ **Use StageIO pattern with manifests** - This is the target state
3. ✅ **Write to io.stage_dir only** - Maintain stage isolation
4. ✅ **Use logger, not print** - Always use proper logging
5. ✅ **Add type hints and docstrings** - 100% compliance required
6. ✅ **Test with standard media samples** - Use samples from § 1.4 🆕
7. ✅ **Implement caching support** - See § 1.6 for patterns 🆕

**When modifying EXISTING code:**
1. 🎯 **Match existing patterns** for consistency
2. 📝 **Add TODO comment** for v3.0 migration if applicable
3. 🔄 **Consider gradual refactoring** if time permits
4. ⚠️ **Note:** Existing stages may not follow StageIO pattern (migration in progress)

**Example for existing stage:**
```python
# TODO: v3.0 - Migrate to StageIO pattern with manifest tracking
# See: scripts/tmdb_enrichment_stage.py for reference implementation
```

---

## 🗺️ Quick Navigation Table

| Task | Section | Topics |
|------|---------|--------|
| Add new stage | § 3.1 | StageIO, manifests, logging |
| Modify config | § 4.2 | .env.pipeline, load_config() |
| Add logging | § 2.3 | Logger usage, log levels |
| Error handling | § 5 | Try/except, error logging |
| Manifest tracking | § 2.5 | Input/output tracking |
| Organize imports | § 6.1 | Standard/Third-party/Local |
| Type hints | § 6.2 | Function signatures |
| Docstrings | § 6.3 | Documentation |
| **Testing** | **§ 1.4** | **Standard test media** 🆕 |
| **Workflows** | **§ 1.5** | **Subtitle/Transcribe/Translate** 🆕 |
| **Caching** | **§ 1.6** | **ML optimization** 🆕 |

**Full standards:** `docs/developer/DEVELOPER_STANDARDS.md`

## 🔒 Automated Enforcement

**Pre-commit Hook Active:**
- ✅ Validates all Python files before commit
- ✅ Blocks commits with violations
- ✅ Maintains 100% compliance automatically
- ✅ See: `docs/PRE_COMMIT_HOOK_GUIDE.md`

---

## 🌲 Decision Trees

### Should I Create a New Stage?

```
Start here:
├─ Is this a distinct transformation step? 
│  ├─ NO → Add to existing stage
│  └─ YES → Continue
│
├─ Can it run independently?
│  ├─ NO → Consider combining with related stage
│  └─ YES → Continue
│
├─ Does it need separate logging/manifest?
│  ├─ NO → Might be a helper function
│  └─ YES → Continue
│
├─ Would it create excessive I/O overhead?
│  ├─ YES → Consider combining stages
│  └─ NO → ✅ CREATE NEW STAGE
│
└─ If YES to all: Follow § 3.1 pattern
```

### What Type of Error Handling Do I Need?

```
Error type:
├─ File not found → FileNotFoundError + logger.error()
├─ Permission denied → PermissionError + logger.error()
├─ Invalid config → ValueError + logger.error()
├─ Network/API → OSError/RequestException + retry logic
├─ Data validation → ValueError + descriptive message
└─ Unknown → Exception + exc_info=True

Always:
├─ Log with logger.error(..., exc_info=True)
├─ Provide context in message
└─ Re-raise or return error code
```

### Where Should This Output Go?

```
Output destination:
├─ Stage processing result?
│  └─ ✅ io.stage_dir / "filename.ext"
│
├─ Temporary/scratch file?
│  └─ ✅ io.stage_dir / "temp" / "file.ext"
│
├─ Final pipeline output?
│  └─ ❌ Write to io.stage_dir, pipeline copies to out/
│
├─ Shared between stages?
│  └─ ❌ Each stage writes own copy, use manifests
│
└─ NEVER:
    ├─ job_dir / "file" (breaks isolation)
    ├─ /tmp/ (unreliable)
    └─ other_stage_dir/ (breaks data lineage)
```

---

## 📚 Topical Index

### By Component

**Configuration (§ 4)**
- Adding parameters → § 4.1, § 4.2
- Loading config → § 4.2
- Type conversion → § 4.3, § 4.4
- Secrets handling → § 4.6
- Validation → § 4.7

**Logging (§ 2)**
- Basic logging → § 2.3
- Stage logs → § 2.4
- Log levels → § 2.3.2
- Performance logging → § 2.3.4
- Error logging → § 2.3.5

**Stages (§ 3)**
- Creating new stage → § 3.1
- StageIO pattern → § 2.6
- Input handling → § 3.2
- Output tracking → § 3.3
- Dependencies → § 3.4

**Data Tracking (§ 2)**
- Manifests → § 2.5
- Input tracking → § 2.5.3
- Output tracking → § 2.5.4
- Data lineage → § 2.8
- Hash computation → § 2.5.2

**Code Quality (§ 6)**
- Import organization → § 6.1
- Type hints → § 6.2
- Docstrings → § 6.3
- Function patterns → § 6.4
- Testing → § 7

### By Task

**I need to...**
- ...add a stage → § 3.1, Decision Tree #1
- ...log something → § 2.3, Critical Rule #1
- ...handle errors → § 5, Decision Tree #2
- ...add config → § 4.1, § 4.2
- ...track files → § 2.5
- ...organize imports → § 6.1, Critical Rule #2
- ...write outputs → § 1.1, Decision Tree #3
- ...validate data → § 5, § 7.2

### By Problem

**Common Issues:**
- "Print not working" → Use logger (§ 2.3)
- "Output not found" → Check io.stage_dir (§ 1.1)
- "Manifest error" → enable_manifest=True (§ 2.6)
- "Config not loading" → Use load_config() (§ 4.2)
- "Import error" → Organize properly (§ 6.1)
- "Permission denied" → Error handling (§ 5)
- "File not tracked" → add_input/output (§ 2.5)

---

## 📂 File Naming Standards

### Stage Script Naming (MANDATORY)

**All stage scripts MUST follow this pattern:**

```
scripts/{NN}_{stage_name}.py
```

Where `NN` is the stage number (01-99) and matches the stage directory name.

**Examples:**

✅ **CORRECT:**
```
scripts/01_demux.py           → Stage directory: 01_demux/
scripts/02_tmdb_enrichment.py → Stage directory: 02_tmdb/
scripts/03_glossary_loader.py → Stage directory: 03_glossary_load/
scripts/04_source_separation.py
scripts/05_pyannote_vad.py
scripts/06_whisperx_asr.py
scripts/07_mlx_alignment.py (or 07_alignment.py)
scripts/08_lyrics_detection.py
scripts/09_hallucination_removal.py
scripts/10_translation.py (or 10_indictrans2_translation.py)
scripts/11_subtitle_generation.py (or 11_subtitle_gen.py)
scripts/12_mux.py
```

❌ **INCORRECT (Old patterns - DO NOT USE):**
```
scripts/demux.py                          # Missing stage number
scripts/tmdb_enrichment_stage.py          # Wrong name (fixed in v6.1)
scripts/03_glossary_load/glossary_loader.py  # Wrong directory
```

**Rules:**
1. ✅ Format: `{NN}_{stage_name}.py`
2. ✅ Place directly in `scripts/` (not in subdirectories)
3. ✅ Match stage directory name (e.g., `01_demux/` → `01_demux.py`)
4. ❌ No `_stage` suffix
5. ❌ No subdirectories for stage scripts

**Utility Scripts (Non-stages):**
```
scripts/config_loader.py      # Helper modules
scripts/device_selector.py
scripts/filename_parser.py
```

---

## 🔧 Job Preparation Flow

### prepare-job Design

**Purpose:** Create job-specific configuration by copying and customizing system defaults.

**Process Flow:**

```
1. Read: config/.env.pipeline (system defaults)
   ↓
2. Create: out/.../job-YYYYMMDD-user-NNNN/ (job directory)
   ↓
3. Copy: config/.env.pipeline → job/.env.pipeline
   ↓
4. Update: job/.env.pipeline with CLI parameters
   ↓
5. Create: job/job.json (job metadata)
```

**Example:**

```bash
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-language en

# Results in:
# 1. job/.env.pipeline (copied from config/.env.pipeline)
# 2. job/.env.pipeline updated with: source_language=hi, target_language=en
# 3. job/job.json created with job metadata
```

**Configuration Files:**

1. **`config/.env.pipeline`** (System defaults)
   - Created by `bootstrap.sh`
   - Version-controlled template
   - Default values for all parameters
   - **NEVER modified during job execution**

2. **`{job_dir}/.env.pipeline`** (Job-specific config)
   - Created by `prepare-job` (copied from system defaults)
   - Updated with CLI parameters
   - Used by all stages during execution
   - Not version-controlled

3. **`{job_dir}/job.json`** (Job metadata)
   - Job ID, workflow, languages, timestamps
   - Created by `prepare-job`
   - Metadata only (not loaded by stages)

**Stage Configuration Access:**

```python
from shared.config_loader import load_config

# In stage scripts:
def run_stage(job_dir: Path, stage_name: str) -> int:
    # Automatically reads from job_dir/.env.pipeline
    config = load_config(job_dir)
    
    # Get configuration values
    model = config.get("WHISPERX_MODEL", "large-v2")
    enabled = config.get("SOURCE_SEPARATION_ENABLED", "true")
```

**Key Points:**
- ✅ `prepare-job` copies config, doesn't read CLI params from job.json
- ✅ Stages read `.env.pipeline`, not `job.json`
- ✅ System config (`config/.env.pipeline`) is never modified
- ✅ Each job has its own `.env.pipeline` copy

---

## 🚨 Critical Rules (NEVER Violate)

### 1. Logger Usage - NOT Print (§ 2.3)

**60% of files violate this - Priority #1 fix**

❌ **DON'T:** `print("message")`

✅ **DO:**
```python
# Stages
io = StageIO("stage", job_dir, enable_manifest=True)
logger = io.get_stage_logger()

# Non-stages
from shared.logger import get_logger
logger = get_logger(__name__)

# Usage
logger.debug("Diagnostic info")
logger.info("General info")
logger.warning("Unexpected situation")
logger.error("Error occurred", exc_info=True)
logger.critical("Severe error")
```

---

### 2. Import Organization (§ 6.1)

**100% of files violate this - Priority #2 fix**

❌ **DON'T:** Mix import groups or use incorrect paths

✅ **DO:**
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np

# Local - MUST use "shared." prefix (AD-007)
from shared.config import load_config
from shared.logger import get_logger
from shared.bias_window_generator import BiasWindow

# Lazy imports - MUST also use "shared." prefix
def some_function():
    try:
        from shared.bias_window_generator import create_bias_windows
        # Use function
    except ImportError:
        logger.warning("Feature unavailable")
```

**🏛️ ARCHITECTURAL DECISION AD-007 (MANDATORY):**

**ALL imports from shared/ directory MUST use "shared." prefix**

**Why This Matters:**
- Python module resolution requires consistent paths
- Lazy imports (try/except) were using incorrect paths
- Fixed Bug #4 (bias window generator import)
- Prevents silent feature degradation

**Common Mistakes:**
```python
# ❌ WRONG - Missing "shared." prefix
from bias_window_generator import BiasWindow
try:
    from config_loader import load_config  # Will fail!
except ImportError:
    pass

# ✅ CORRECT - Always use "shared." prefix
from shared.bias_window_generator import BiasWindow
try:
    from shared.config_loader import load_config  # Works!
except ImportError:
    pass
```

**Order:** Standard → Third-party → Local (blank lines between)

**Applies To:** All scripts, stages, and tests

---

### 3. StageIO Pattern (§ 2.6)

**Every stage MUST:**

```python
#!/usr/bin/env python3
# Standard library
import sys
from pathlib import Path

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import load_config
from shared.stage_utils import StageIO

def run_stage(job_dir: Path, stage_name: str = "stage") -> int:
    # 1. Initialize with manifest
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        # 2. Load config
        config = load_config()
        
        # 3. Find input
        input_file = io.job_dir / "prev_stage" / "input.ext"
        io.manifest.add_input(input_file, io.compute_hash(input_file))
        
        # 4. Define output in stage dir ONLY
        output_file = io.stage_dir / "output.ext"
        
        # 5. Process
        logger.info("Processing...")
        
        # 6. Track output
        io.manifest.add_output(output_file, io.compute_hash(output_file))
        
        # 6a. Track intermediate files (NEW in v6.1)
        intermediate_file = io.stage_dir / "cache.tmp"
        io.track_intermediate(intermediate_file, retained=True, reason="Model cache")
        
        # 7. Finalize
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
```

**Must have:**
- `enable_manifest=True`
- `io.get_stage_logger()` (not print)
- Track inputs/outputs
- Track intermediate files (NEW in v6.1) - Use `io.track_intermediate()` for cache/temp files
- Write to `io.stage_dir` ONLY
- Finalize manifest

**StageManifest Methods (v6.1):**
```python
# Track inputs
io.manifest.add_input("key", file_path, "description")

# Track outputs  
io.manifest.add_output("key", file_path, "description")

# Track intermediate files (NEW in v6.1)
io.track_intermediate(file_path, retained=True, reason="Model cache")
# retained=True: Keep after stage completes
# retained=False: Temporary file (can be deleted)
```

---

### 4. Configuration (§ 4)

❌ **DON'T:** `os.getenv()` or `os.environ[]`

✅ **DO:**
```python
from shared.config_loader import load_config
import json

# Step 1: Load system defaults
config = load_config()
value = int(config.get("PARAM_NAME", default))

# Step 2: Override with job-specific parameters (MANDATORY - AD-006)
job_json_path = job_dir / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
        # Job parameters take precedence
        if 'param_name' in job_data and job_data['param_name']:
            value = job_data['param_name']
```

**🏛️ ARCHITECTURAL DECISION AD-006 (MANDATORY):**

**ALL stages MUST honor job-specific parameters over system defaults.**

**Priority Order:**
1. **job.json** (user's explicit CLI choices)
2. **Job .env file** (job-specific overrides)
3. **System config/.env.pipeline** (system defaults)
4. **Code defaults** (hardcoded fallbacks)

**Why This Is Mandatory:**
- Respect user's explicit CLI parameters
- Enable per-job customization
- Ensure reproducibility
- Fixed Bug #3 (language detection)

**Parameters That Must Be Overridable:**
- ✅ Languages (source_language, target_languages)
- ✅ Model settings (model size, compute type, batch size)
- ✅ Quality settings (beam size, temperature)
- ✅ Workflow flags (source_separation_enabled, tmdb_enabled)
- ✅ Output preferences (subtitle format, translation engine)

**See:** ARCHITECTURE_ALIGNMENT_2025-12-04.md § AD-006 for complete rationale.

**Steps:**
1. Add to `config/.env.pipeline` with full documentation
2. Use `load_config()` to get system defaults
3. Read job.json and override if parameter exists
4. Provide default with `.get(key, default)`
5. Convert types: int(), float(), bool()

**Configuration Parameter Rules:**
- ✅ **Implement feature FIRST, then add parameter**
- ✅ **Remove unused parameters immediately**  
- ✅ **Mark future features**: `Status: ⏳ NOT YET IMPLEMENTED`
- ✅ **Full documentation**: Purpose, values, defaults, impact
- ❌ **NEVER add without implementation**
- ❌ **NEVER leave unused parameters**

---

### 5. Error Handling (§ 5)

```python
try:
    risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}", exc_info=True)
    raise
except PermissionError as e:
    logger.error(f"Permission denied: {e}", exc_info=True)
    raise
except Exception as e:
    logger.error(f"Unexpected: {e}", exc_info=True)
    raise RuntimeError(f"Failed: {e}")
```

**Key:** Specific exceptions first, always `exc_info=True`

**⚠️ COMMON MISTAKE - AVOID:**
```python
# ❌ WRONG - Duplicate parameter (SyntaxError)
logger.error(f"Error: {e}", exc_info=True, exc_info=True)

# ✅ CORRECT - Single parameter
logger.error(f"Error: {e}", exc_info=True)
```

**Note:** This error occurred in job-20251203-rpatel-0015 and caused pipeline failure. Always use `exc_info=True` exactly once.

---

### 6. Stage Directory Containment (§ 1.1)

❌ **DON'T:**
```python
output = job_dir / "file.ext"  # Wrong: job root
output = Path("/tmp/file.ext")  # Wrong: /tmp
```

✅ **DO:**
```python
output = io.stage_dir / "file.ext"  # Correct: stage dir only
```

---

## 🖥️ Cross-Platform Requirements (§ 1.2)

**ALL core scripts MUST have Windows equivalents:**

| Script | Unix/macOS | Windows | Status |
|--------|------------|---------|--------|
| bootstrap | ✅ `.sh` | ✅ `.ps1` | Complete |
| prepare-job | ✅ `.sh` | ✅ `.ps1` | Complete |
| run-pipeline | ✅ `.sh` | ✅ `.ps1` | Complete |
| test-glossary-quickstart | ✅ `.sh` | ✅ `.ps1` | Complete |

**When creating NEW shell scripts:**
1. Create `.sh` for Unix/Linux/macOS
2. Create `.ps1` for Windows (PowerShell 5.1+)
3. Test on both platforms or document limitations
4. Use platform-agnostic patterns where possible

**Python code MUST be cross-platform:**
```python
# ✅ GOOD - Cross-platform paths
from pathlib import Path
config_path = Path("config") / ".env.pipeline"

# ❌ BAD - Unix-only
config_path = "config/.env.pipeline"

# ✅ GOOD - Platform detection
import sys
if sys.platform == "win32":
    # Windows-specific code
else:
    # Unix-like systems
```

---

## 📋 Pre-Commit Checklist

**Before proposing code, verify:**

**ALL code:**
- [ ] Logger, not print (§ 2.3)
- [ ] Imports organized (§ 6.1)
- [ ] Type hints (§ 6.2)
- [ ] Docstrings (§ 6.3)
- [ ] Error handling (§ 5)
- [ ] Cross-platform compatible (§ 1.2)

**STAGE code:**
- [ ] File named `{NN}_{stage_name}.py` (File Naming)
- [ ] File in `scripts/` directory (not subdirectory)
- [ ] `enable_manifest=True` (§ 2.6)
- [ ] `io.get_stage_logger()` (§ 2.3)
- [ ] Track inputs (§ 2.5)
- [ ] Track outputs (§ 2.5)
- [ ] Write to `io.stage_dir` only (§ 1.1)
- [ ] Finalize manifest (§ 2.6)
- [ ] Context propagation implemented (§ 1.5) 🆕
- [ ] Cache-aware processing (§ 1.6) 🆕

**TEST code:** 🆕
- [ ] Uses standard test media (§ 1.4)
- [ ] Tests Sample 1 (English technical) OR Sample 2 (Hinglish)
- [ ] Validates quality baselines
- [ ] Tests relevant workflow (Subtitle/Transcribe/Translate)
- [ ] Tests caching behavior (first run vs. cached)
- [ ] Includes integration test if workflow modified

**SHELL scripts:**
- [ ] Unix (.sh) script created
- [ ] Windows (.ps1) script created
- [ ] Both scripts have same functionality
- [ ] Both scripts tested (or documented as untested)

**CONFIG changes:**
- [ ] Parameter is actually USED in code (not planned)
- [ ] Searched codebase to confirm usage
- [ ] Added to `.env.pipeline` with full documentation (§ 4.1)
- [ ] Uses `load_config()` in code (§ 4.2)
- [ ] Has default value (§ 4.3)
- [ ] If future feature: Marked with `⏳ NOT YET IMPLEMENTED`

**Dependencies:**
- [ ] Added to `requirements/*.txt` (§ 1.3)

**DOCUMENTATION (NEW FEATURES):** 🆕
- [ ] **New feature (>200 LOC):** BRD-PRD-TRD created (DEVELOPER_STANDARDS.md § 21)
- [ ] **Architectural change:** AD documented in ARCHITECTURE.md
- [ ] **PRD:** User stories with acceptance criteria written
- [ ] **PRD:** User personas defined (at least 2-3)
- [ ] **PRD:** Links to BRD and TRD included
- [ ] **Implementation Tracker:** Task linked to BRD/PRD/TRD
- [ ] **Post-implementation:** Mark BRD/PRD/TRD as "Implemented"

**Run automated checker:**
```bash
./scripts/validate-compliance.py your_file.py
```

---

## 🎯 Common Patterns

### Multiple Inputs
```python
for f in input_dir.glob("*.wav"):
    io.manifest.add_input(f, io.compute_hash(f))
```

### Config Types
```python
config = load_config()
int_val = int(config.get("MAX_DURATION", 3600))
float_val = float(config.get("THRESHOLD", 0.85))
bool_val = config.get("ENABLED", "true").lower() == "true"
list_val = config.get("LANGS", "en,hi").split(",")
```

### Progress Logging
```python
for i, item in enumerate(items):
    if i % 100 == 0:
        logger.info(f"Progress: {i}/{len(items)} ({i/len(items)*100:.0f}%)")
```

### Performance Logging
```python
import time
start = time.time()
result = expensive_op()
logger.info(f"Completed in {time.time()-start:.2f}s")
```

---

## 🏗️ Tech Stack

- **Python:** 3.11+
- **Stages:** 01_demux, 02_tmdb, etc.
- **I/O:** `shared/stage_utils.py`
- **Config:** `config/.env.pipeline`
- **Logging:** Main + stage logs

---

## 🔗 References

**Complete standards:** `docs/developer/DEVELOPER_STANDARDS.md`

**Sections:**
- § 1: Project structure
- § 2: Logging & manifests
- § 3: Stages
- § 4: Configuration
- § 5: Error handling
- § 6: Code style
- § 7: Testing

**Guides:**
- **`docs/CODE_EXAMPLES.md`** - ⭐ Good vs Bad code examples (941 lines)
- `docs/developer-guide.md` - Onboarding
- `docs/BASELINE_COMPLIANCE_METRICS.md` - Current state
- `docs/AI_MODEL_ROUTING.md` - Model selection

---

## 🤖 Automated Validation

**Pre-commit Hook: ✅ ACTIVE**

The pre-commit hook automatically validates all staged Python files:
```bash
# Hook runs automatically on commit
git commit -m "Your message"
# → Hook validates Python files
# → Blocks if violations found
# → Commits if all pass
```

**Manual Validation:**
```bash
# Single file
python3 scripts/validate-compliance.py scripts/your_stage.py

# Multiple files
python3 scripts/validate-compliance.py scripts/*.py

# Strict mode (exit 1 on violations)
python3 scripts/validate-compliance.py --strict scripts/*.py

# Check staged files
python3 scripts/validate-compliance.py --staged
```

**Hook Setup (for new clones):**
```bash
cp tools/pre-commit-hook-template.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Full Guide:** `docs/PRE_COMMIT_HOOK_GUIDE.md`

---

## 📊 Status

**Achievement:** 🎊 **100% PERFECT COMPLIANCE** 🎊

**All Categories (100%):**
- ✅ Type hints: 100% (140+ added)
- ✅ Docstrings: 100% (80+ added)
- ✅ Logger usage: 100% (no print statements)
- ✅ Import organization: 100% (Standard/Third-party/Local)
- ✅ Config patterns: 100% (load_config() everywhere)
- ✅ Error handling: 100% (proper try/except)

**Files:** 69/69 (100% compliant) | **Violations:** 0 critical, 0 errors, 0 warnings

---

## 📚 BRD-PRD-TRD Framework Quick Reference

**When to Create:** (DEVELOPER_STANDARDS.md § 21)

**MANDATORY:**
- 🔥 New features (>200 LOC or new functionality)
- 🔥 Architectural changes (new ADs)
- 🔥 Breaking changes (API changes)

**RECOMMENDED:**
- 🟡 Medium features (50-200 LOC)
- 🟡 Bug fixes changing user behavior

**OPTIONAL:**
- 🟢 Small fixes (<50 LOC)
- 🟢 Documentation-only changes

**Creation Flow:**
```
1. BRD: Business justification (WHY)
   - Problem statement, business value, stakeholders
   - Template: docs/requirements/brd/BRD_TEMPLATE.md
   
2. PRD: User requirements (WHAT)
   - User stories, personas, acceptance criteria
   - Template: docs/requirements/prd/PRD_TEMPLATE.md
   
3. TRD: Technical design (HOW)
   - Architecture, APIs, implementation
   - Template: docs/requirements/trd/TRD_TEMPLATE.md
   
4. Implementation: Code + Tests + Docs
   - Follow TRD design
   - Validate against PRD acceptance criteria
   - Update IMPLEMENTATION_TRACKER.md
```

**Example PRDs:**
- PRD-2025-12-05-02-workflow-outputs.md (591 lines)
- PRD-2025-12-08-05-subtitle-workflow.md (530 lines)
- PRD-2025-12-08-03-log-management.md (227 lines)

**Complete Guide:**
- Framework: BRD-PRD-TRD-IMPLEMENTATION-FRAMEWORK.md
- Examples: docs/requirements/prd/
- Standards: DEVELOPER_STANDARDS.md § 21

---

## 🚀 Testing

- Tests in `tests/`
- Run: `pytest tests/`
- Unit: fast (no GPU)
- Coverage: `pytest --cov`

---

**When in doubt:**
1. Run the mental checklist at the top
2. Use decision trees above
3. **Check CODE_EXAMPLES.md for visual examples** ⭐
4. Check § reference in DEVELOPER_STANDARDS.md
5. Run `validate-compliance.py` on your code
6. **Commit will be blocked if violations exist** 🔒

**Version:** 7.2 (BRD-PRD-TRD Framework) | **Lines:** 1600+ | **Status:** ✅ PERFECT | **Automated:** ✅
