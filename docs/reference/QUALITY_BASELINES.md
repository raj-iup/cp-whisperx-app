# Quality Baselines for Standard Test Media

**Version:** 1.0  
**Last Updated:** 2025-12-03  
**Purpose:** Define expected quality metrics for regression testing

---

## Overview

This document establishes quality baselines for the two standard test media samples. These baselines are used for:
- Regression testing (detect quality degradation)
- Performance benchmarking
- CI/CD quality gates
- Model/algorithm comparison

---

## Sample 1: English Technical Content

**File:** `in/Energy Demand in AI.mp4`  
**Duration:** 2-5 minutes  
**Language:** English  
**Type:** Technical/Educational

### ASR Quality Targets

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| Word Error Rate (WER) | ≤5% | ≤8% | Clean audio, single speaker |
| Proper Noun Accuracy | ≥90% | ≥85% | Technical terms, names |
| Technical Term Accuracy | ≥95% | ≥90% | AI, energy, demand, etc. |
| Word-level Alignment | ±50ms | ±100ms | Timestamp accuracy |

### Translation Quality Targets (English → Hindi)

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| BLEU Score | ≥90% | ≥85% | IndicTrans2 model |
| Fluency | ≥90% | ≥85% | Grammatical correctness |
| Term Preservation | 100% | ≥95% | Technical terms transliterated |
| Cultural Adaptation | ≥85% | ≥80% | Context-appropriate |

### Translation Quality Targets (English → Spanish)

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| BLEU Score | ≥88% | ≥83% | NLLB model |
| Fluency | ≥85% | ≥80% | Grammatical correctness |
| Term Preservation | 100% | ≥95% | Technical terms preserved |

### Performance Targets

| Stage | Target Time | Max Time | Notes |
|-------|-------------|----------|-------|
| 01_demux | <10s | <20s | Audio extraction |
| 06_whisperx_asr | <2 min | <5 min | Depends on model size |
| 07_alignment | <30s | <60s | Word-level alignment |
| 08_translation | <1 min | <2 min | Per language |
| **Total Pipeline** | **<5 min** | **<10 min** | Transcribe workflow |

---

## Sample 2: Hinglish Bollywood Content

**File:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Duration:** 1-3 minutes  
**Language:** Hindi/Hinglish (code-mixed)  
**Type:** Entertainment/Bollywood

### ASR Quality Targets

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| Word Error Rate (WER) | ≤15% | ≤20% | Code-mixing challenge |
| Character Name Accuracy | ≥90% | ≥85% | Via glossary |
| Code-mixing Handling | ≥80% | ≥75% | Hindi-English mix |
| Devanagari Script Output | 100% | 100% | Native script for Hindi |
| Speaker Diarization | ≥85% | ≥80% | Multiple speakers |

### Subtitle Quality Targets

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| Subtitle Quality Score | ≥88% | ≥85% | Overall quality |
| Timing Accuracy | ±200ms | ±300ms | Subtitle synchronization |
| Reading Speed (CPS) | 15-17 | 12-18 | Characters per second |
| Line Length | ≤42 chars | ≤45 chars | Per line |
| Max Lines | 2 | 2 | Per subtitle frame |

### Context-Aware Features

| Feature | Target | Acceptable | Notes |
|---------|--------|------------|-------|
| Glossary Application Rate | 100% | ≥95% | All glossary terms used |
| Character Name Preservation | 100% | ≥95% | Jai, Aditi, Meow, etc. |
| Cultural Term Handling | ≥90% | ≥85% | beta, bhai, ji, yaar |
| Temporal Coherence | ≥80% | ≥75% | Consistent terminology |
| Formality Level | ≥85% | ≥80% | Casual speech maintained |

### Translation Quality Targets (Hindi → English)

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| BLEU Score | ≥90% | ≥85% | Hindi-to-English |
| Fluency | ≥88% | ≥83% | Natural English |
| Cultural Adaptation | ≥80% | ≥75% | Idioms, metaphors |
| Character Name Preservation | 100% | ≥95% | Names unchanged |
| Formality Maintenance | ≥85% | ≥80% | Casual tone preserved |

### Translation Quality Targets (Hindi → Gujarati, Indic-to-Indic)

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| BLEU Score | ≥88% | ≥83% | IndicTrans2 |
| Fluency | ≥88% | ≥83% | Native Gujarati |
| Script Consistency | 100% | 100% | Devanagari → Gujarati |
| Cultural Context | ≥90% | ≥85% | Preserved |

### Translation Quality Targets (Hindi → Spanish, Indic-to-non-Indic)

| Metric | Target | Acceptable | Notes |
|--------|--------|------------|-------|
| BLEU Score | ≥85% | ≥80% | NLLB model |
| Fluency | ≥82% | ≥77% | Natural Spanish |
| Cultural Adaptation | ≥75% | ≥70% | Cross-cultural |
| Name Transliteration | 100% | ≥95% | Proper names |

### Performance Targets (Full Subtitle Pipeline)

| Stage | Target Time | Max Time | Notes |
|-------|-------------|----------|-------|
| 01_demux | <10s | <20s | Audio extraction |
| 02_tmdb | <5s | <10s | Metadata lookup |
| 03_glossary_load | <5s | <10s | Load terms |
| 04_source_separation | <30s | <60s | Optional |
| 05_pyannote_vad | <15s | <30s | Voice activity |
| 06_whisperx_asr | <2 min | <5 min | ASR + alignment |
| 07_alignment | <15s | <30s | If separate |
| 08_translation | <1 min/lang | <2 min/lang | Per target language |
| 09_subtitle_gen | <30s | <60s | All languages |
| 10_mux | <15s | <30s | Soft-embed subtitles |
| **Total Pipeline (1 lang)** | **<6 min** | **<12 min** | Single target language |
| **Total Pipeline (4 langs)** | **<10 min** | **<20 min** | en, gu, ta, es |

---

## Measurement Methodology

### ASR Accuracy (WER)

```python
from jiwer import wer

# Reference transcript (ground truth)
reference = "This is a test transcript"

# Hypothesis transcript (system output)
hypothesis = "This is a test transcrit"

# Calculate WER
error_rate = wer(reference, hypothesis)
wer_percent = error_rate * 100
```

### Translation Quality (BLEU)

```python
from sacrebleu import corpus_bleu

# Reference translations (list of ground truth)
references = [["This is a reference translation"]]

# System translations (list of outputs)
hypotheses = ["This is a system translation"]

# Calculate BLEU
bleu = corpus_bleu(hypotheses, references)
bleu_score = bleu.score  # 0-100
```

### Subtitle Timing Accuracy

```python
import numpy as np

# Reference subtitle timings
ref_timings = [(0.0, 2.5), (2.5, 5.0), ...]

# System subtitle timings
sys_timings = [(0.1, 2.6), (2.4, 4.9), ...]

# Calculate mean absolute error
errors = []
for (ref_start, ref_end), (sys_start, sys_end) in zip(ref_timings, sys_timings):
    errors.append(abs(ref_start - sys_start))
    errors.append(abs(ref_end - sys_end))

mean_error_ms = np.mean(errors) * 1000
```

### Glossary Application Rate

```python
# Count glossary terms in source
glossary_terms = ["Jai", "Aditi", "Meow", "beta", "bhai"]
source_text = "Jai and Aditi are friends, beta."

terms_found = sum(1 for term in glossary_terms if term in source_text)
total_terms = len(glossary_terms)

application_rate = terms_found / total_terms * 100
```

---

## Baseline Establishment Process

### 1. Initial Baseline Measurement

Run each workflow with standard test media:

```bash
# Sample 1: Transcribe
./prepare-job.sh --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe --source-language en
./run-pipeline.sh --job-dir out/LATEST

# Sample 2: Subtitle (full pipeline)
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle --source-language hi \
  --target-languages en,gu,ta,es
./run-pipeline.sh --job-dir out/LATEST
```

### 2. Measure Quality Metrics

- Manually verify ASR output against ground truth
- Calculate WER, BLEU, timing accuracy
- Review glossary application
- Check context-aware features

### 3. Record Baselines

- Document measurements in this file
- Store reference outputs in `tests/fixtures/baselines/`
- Create automated tests that compare against baselines

### 4. Update Baselines

Update baselines when:
- ✅ Intentional quality improvements
- ✅ Model upgrades (document version change)
- ✅ Algorithm improvements
- ❌ NOT for quality degradation

---

## Regression Testing

### Automated Tests

```python
@pytest.mark.quality_baseline
def test_sample1_asr_meets_baseline():
    """Test Sample 1 ASR meets WER baseline."""
    wer = measure_asr_quality("sample1")
    assert wer <= 0.05, f"WER {wer:.1%} exceeds baseline of 5%"

@pytest.mark.quality_baseline
def test_sample2_subtitle_quality_meets_baseline():
    """Test Sample 2 subtitle quality meets baseline."""
    quality = measure_subtitle_quality("sample2")
    assert quality >= 0.88, f"Quality {quality:.1%} below baseline of 88%"
```

### CI/CD Integration

Quality baseline tests run in CI/CD:
- On pull requests (warn if below acceptable)
- On main branch (fail if below acceptable)
- Weekly scheduled runs (monitor trends)

---

## Baseline History

| Date | Sample | Metric | Value | Model/Algorithm | Notes |
|------|--------|--------|-------|-----------------|-------|
| 2025-12-03 | Sample 1 | WER | TBD | Whisper large-v3 | Initial baseline |
| 2025-12-03 | Sample 1 | BLEU (Hi) | TBD | IndicTrans2 | Initial baseline |
| 2025-12-03 | Sample 2 | WER | TBD | Whisper large-v3 | Initial baseline |
| 2025-12-03 | Sample 2 | Subtitle Quality | TBD | Full pipeline | Initial baseline |

**Note:** TBD values will be populated after first full pipeline run with models.

---

## Quality Gates

### CI/CD Quality Gates

**Pull Requests:**
- WARN if quality drops below "Acceptable" threshold
- FAIL if quality drops below "Acceptable" - 10%
- PASS with comment showing quality metrics

**Main Branch:**
- FAIL if quality drops below "Acceptable" threshold
- Require manual override with justification

**Releases:**
- All metrics must meet "Target" thresholds
- Document any deviations in release notes

---

## Future Enhancements

### Additional Samples

Consider adding:
- **Arabic content** - RTL script handling
- **Chinese content** - Character-based language
- **Russian content** - Cyrillic script
- **Noisy audio** - Background noise handling
- **Accented speech** - Dialect variations
- **Multi-speaker** - Conference/interview style

### Additional Metrics

- **Hallucination rate** (ASR false positives)
- **Cultural sensitivity score** (appropriate translations)
- **Temporal coherence score** (terminology consistency)
- **Reading speed compliance** (CPS within range)
- **Line length compliance** (characters per line)

---

**END OF QUALITY BASELINES DOCUMENT**
