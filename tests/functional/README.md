# Functional Tests

**Purpose:** End-to-end workflow validation

---

## Overview

Functional tests validate complete workflows from start to finish, testing the entire pipeline with real data and dependencies. These are the slowest tests but provide the highest confidence in system behavior.

---

## Test Categories

### Workflow Tests
- `test_transcribe_workflow.py` - Complete transcribe workflow
- `test_translate_workflow.py` - Complete translate workflow
- `test_subtitle_workflow.py` - Complete subtitle workflow

### Quality Tests
- `test_quality_metrics.py` - ASR WER, Translation BLEU, Subtitle Quality

### Performance Tests
- `test_performance_benchmarks.py` - Processing speed, resource usage

---

## Writing Functional Tests

### Template
```python
import pytest
from pathlib import Path


@pytest.mark.slow
@pytest.mark.functional
class TestTranscribeWorkflow:
    """Test complete transcribe workflow."""
    
    def test_english_audio(self):
        """Test English audio transcription."""
        # Use standard test media
        input_file = Path("tests/fixtures/audio/sample_en.wav")
        
        # Run complete workflow
        result = run_transcribe_workflow(
            media_file=input_file,
            language="en"
        )
        
        # Verify success
        assert result.exit_code == 0
        
        # Verify output exists
        transcript_file = result.job_dir / "07_alignment" / "transcript.txt"
        assert transcript_file.exists()
        
        # Verify quality
        wer = calculate_wer(transcript_file, expected_transcript)
        assert wer < 0.05, f"WER {wer} exceeds 5% threshold"
    
    def test_hinglish_audio(self):
        """Test Hinglish audio transcription."""
        input_file = Path("tests/fixtures/video/sample_hinglish.mp4")
        
        result = run_transcribe_workflow(
            media_file=input_file,
            language="hi"
        )
        
        assert result.exit_code == 0
        assert result.wer < 0.15  # 15% threshold for Hinglish
```

---

## Test Fixtures

Use standard test media from `tests/fixtures/`:
- `audio/sample_en.wav` - English audio
- `video/sample_hinglish.mp4` - Hinglish video
- `expected/sample_en_transcript.txt` - Expected transcript

---

## Running Functional Tests

```bash
# All functional tests (slow)
pytest tests/functional/ -v

# Skip slow tests
pytest tests/functional/ -m "not slow" -v

# Single test
pytest tests/functional/test_transcribe_workflow.py::TestTranscribeWorkflow::test_english_audio -v

# With output capture
pytest tests/functional/ -v -s
```

---

## Quality Thresholds

### ASR Accuracy
- English: WER ≤5%
- Hindi: WER ≤15%
- Hinglish: WER ≤20%

### Translation Quality
- IndicTrans2: BLEU ≥90%
- NLLB-200: BLEU ≥85%

### Subtitle Quality
- Overall: ≥88%
- Temporal coherence: ≥90%
- Context awareness: ≥80%

---

## Best Practices

### DO:
- ✅ Mark with `@pytest.mark.slow`
- ✅ Mark with `@pytest.mark.functional`
- ✅ Use standard test media
- ✅ Test complete workflows
- ✅ Validate quality metrics
- ✅ Clean up output files

### DON'T:
- ❌ Test implementation details
- ❌ Run in CI for every commit (too slow)
- ❌ Use real production data
- ❌ Skip cleanup

---

**See Also:**
- **tests/README.md** - Main testing guide
- **tests/fixtures/README.md** - Test data guide
- **AD-013** - Test organization architecture

---

**Last Updated:** 2025-12-08
