# Test Fixtures

**Purpose:** Shared test data and expected outputs

---

## Overview

Test fixtures provide standardized test data used across all test types (unit, integration, functional). This ensures consistent, reproducible testing.

---

## Directory Structure

```
tests/fixtures/
├── README.md           # This file
├── audio/              # Sample audio files
│   ├── sample_en.wav          # English audio (clean)
│   ├── sample_hi.wav          # Hindi audio
│   └── sample_hinglish.mp4    # Hinglish mixed audio
├── video/              # Sample video files
│   ├── sample_en.mp4          # English video with audio
│   └── sample_hinglish.mp4    # Hinglish Bollywood clip
└── expected/           # Expected test outputs
    ├── sample_en_transcript.txt
    ├── sample_en_aligned.json
    └── sample_en_translation_hi.txt
```

---

## Standard Test Media

### Sample 1: English Technical Content
**File:** `audio/sample_en.wav` or `video/sample_en.mp4`  
**Language:** English  
**Type:** Technical/Educational  
**Duration:** 2-5 minutes  
**Use For:** Transcribe, Translate workflows

**Characteristics:**
- Clear English audio
- Technical terminology (AI, energy, demand)
- Minimal background noise
- Good for ASR accuracy testing

**Quality Targets:**
- ASR Accuracy: ≥95% WER
- Translation BLEU: ≥90%
- Processing Time: <3 minutes

### Sample 2: Hinglish Bollywood Content
**File:** `video/sample_hinglish.mp4`  
**Language:** Hindi/Hinglish (mixed)  
**Type:** Entertainment  
**Duration:** 1-3 minutes  
**Use For:** Subtitle, Transcribe, Translate workflows

**Characteristics:**
- Mixed Hindi-English dialogue
- Bollywood speech patterns
- Multiple speakers possible
- Real-world subtitle challenge

**Quality Targets:**
- ASR Accuracy: ≥85% WER
- Subtitle Quality: ≥88%
- Context Awareness: ≥80%

---

## Using Fixtures in Tests

### Unit Tests
```python
from pathlib import Path

def test_audio_processing():
    """Test audio processing with fixture."""
    audio_file = Path("tests/fixtures/audio/sample_en.wav")
    result = process_audio(audio_file)
    assert result.success
```

### Integration Tests
```python
def test_transcribe_with_alignment():
    """Test transcription and alignment."""
    input_file = Path("tests/fixtures/video/sample_en.mp4")
    expected_file = Path("tests/fixtures/expected/sample_en_transcript.txt")
    
    result = transcribe_and_align(input_file)
    
    with open(expected_file) as f:
        expected = f.read()
    
    similarity = calculate_similarity(result.transcript, expected)
    assert similarity > 0.95
```

### Functional Tests
```python
@pytest.mark.slow
def test_complete_workflow():
    """Test complete workflow with fixture."""
    media_file = Path("tests/fixtures/video/sample_hinglish.mp4")
    
    result = run_subtitle_workflow(
        media_file=media_file,
        source_lang="hi",
        target_langs=["en", "es"]
    )
    
    assert result.exit_code == 0
    assert result.output_file.exists()
```

---

## Adding New Fixtures

### Audio Files
- Format: WAV (16kHz, mono preferred) or MP3
- Duration: 1-5 minutes (keep small for CI)
- Quality: Clear audio, minimal noise
- Naming: `sample_{lang}_{detail}.wav`

### Video Files
- Format: MP4 (H.264 video, AAC audio)
- Duration: 1-5 minutes
- Size: <50MB (for git LFS or external storage)
- Naming: `sample_{lang}_{detail}.mp4`

### Expected Outputs
- Format: Match actual output format (txt, json, srt)
- Generate: Run pipeline once, verify, save as expected
- Naming: `sample_{lang}_{type}.{ext}`

---

## Git LFS (Large Files)

For large fixtures (>10MB), use Git LFS:

```bash
# Track large files
git lfs track "tests/fixtures/video/*.mp4"

# Commit .gitattributes
git add .gitattributes
git commit -m "Track video fixtures with Git LFS"
```

---

## Fixture Best Practices

### DO:
- ✅ Use standard fixtures across tests
- ✅ Keep fixtures small (<50MB each)
- ✅ Document fixture characteristics
- ✅ Version control fixtures
- ✅ Provide both audio and video samples

### DON'T:
- ❌ Commit large files without Git LFS
- ❌ Use production/private data
- ❌ Generate fixtures dynamically
- ❌ Modify fixtures during tests

---

## Current Fixtures

### Available
- ✅ Sample English audio (real file in `in/`)
- ✅ Sample Hinglish video (real file in `in/test_clips/`)

### Needed
- ⏳ Extracted WAV files in fixtures/audio/
- ⏳ Expected transcripts in fixtures/expected/
- ⏳ Expected alignments in fixtures/expected/
- ⏳ Expected translations in fixtures/expected/

---

## Maintenance

### Adding Fixtures
1. Create fixture file in appropriate directory
2. Document in this README
3. Add to git (use LFS for large files)
4. Generate expected outputs
5. Update tests to use new fixture

### Updating Fixtures
1. Document reason for update
2. Update fixture file
3. Regenerate expected outputs
4. Update tests if needed
5. Verify all tests still pass

---

**See Also:**
- **tests/README.md** - Main testing guide
- **docs/user-guide/workflows.md** - Standard test media documentation
- **AD-013** - Test organization architecture

---

**Last Updated:** 2025-12-08
