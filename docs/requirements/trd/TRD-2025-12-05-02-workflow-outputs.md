# TRD: Workflow-Specific Output Requirements

**ID:** TRD-2025-12-05-02  
**Created:** 2025-12-05  
**Status:** Approved  
**Related BRD:** [BRD-2025-12-05-02](../brd/BRD-2025-12-05-02-workflow-outputs.md)

---

## Technical Overview

Implement workflow-aware stage selection in run-pipeline to produce only requested outputs.

---

## Implementation Requirements

### Code Changes

**File:** `run-pipeline.py`

```python
def _execute_transcribe_workflow(self):
    """Transcribe: Source → Source Text ONLY"""
    stages = [
        ("demux", self._stage_demux),
        ("glossary_load", self._stage_glossary_load),
        ("pyannote_vad", self._stage_pyannote_vad),
        ("whisperx_asr", self._stage_whisperx_asr),
        ("alignment", self._stage_alignment),
        ("export_transcript", self._export_transcript),  # NEW
    ]
    # Skip subtitle_generation and mux
    
def _execute_translate_workflow(self):
    """Translate: Source → Target Text ONLY"""
    stages = [
        # ... same as transcribe ...
        ("translation", self._stage_translation),
        ("export_translation", self._export_translated_transcript),  # NEW
    ]
    # Skip subtitle_generation and mux
    
def _execute_subtitle_workflow(self):
    """Subtitle: Full pipeline with embedded subtitles"""
    stages = [
        # ... all 12 stages ...
        ("subtitle_generation", self._stage_subtitle_generation),
        ("mux", self._stage_mux),
    ]
```

### New Methods

```python
def _export_transcript(self):
    """Export plain text transcript"""
    alignment_dir = self.job_dir / "07_alignment"
    transcript_file = alignment_dir / "transcript.txt"
    # Write transcript text
    
def _export_translated_transcript(self):
    """Export translated text transcript"""
    translation_dir = self.job_dir / "10_translation"
    for lang in target_languages:
        output_file = translation_dir / f"transcript_{lang}.txt"
        # Write translated text
```

---

## Testing Requirements

### Functional Tests
```bash
# tests/functional/test_workflow_outputs.py

def test_transcribe_no_subtitles():
    """Verify transcribe creates NO subtitle files"""
    result = run_transcribe_workflow("sample.mp4")
    assert (job_dir / "07_alignment" / "transcript.txt").exists()
    assert not (job_dir / "11_subtitle_generation").exists()
    assert not (job_dir / "12_mux").exists()

def test_translate_no_subtitles():
    """Verify translate creates NO subtitle files"""
    result = run_translate_workflow("sample.mp4", "hi", "en")
    assert (job_dir / "10_translation" / "transcript_en.txt").exists()
    assert not (job_dir / "11_subtitle_generation").exists()
    
def test_subtitle_creates_subtitles():
    """Verify ONLY subtitle workflow creates subtitles"""
    result = run_subtitle_workflow("sample.mp4", "hi", ["en", "es"])
    assert (job_dir / "12_mux" / "output.mkv").exists()
    assert has_subtitle_tracks(result.output_file, ["en", "es"])
```

---

## Documentation Updates

- [ ] User Guide: Update workflow descriptions
- [ ] README.md: Update output examples
- [ ] ARCHITECTURE.md: AD-010 section
- [ ] Copilot Instructions: Workflow-specific patterns

---

## Performance Considerations

**Expected Impact:**
- Transcribe: 15-20% faster (skip 2 stages)
- Translate: 20-30% faster (skip 2 stages)
- Subtitle: No change (full pipeline)

---

## Related Documents

- **BRD:** [BRD-2025-12-05-02-workflow-outputs.md](../brd/BRD-2025-12-05-02-workflow-outputs.md)
- **AD-010:** ARCHITECTURE.md § AD-010

---

**Version:** 1.0 | **Status:** Approved (Pending Implementation)
