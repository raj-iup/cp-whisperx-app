# Testing Guide

**Version:** 1.0  
**Last Updated:** 2025-12-03  
**Status:** Production Ready

---

## Overview

This document provides comprehensive instructions for running, writing, and maintaining tests for the CP-WhisperX pipeline.

---

## Quick Start

### Run All Tests

```bash
# Run all non-slow tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=scripts --cov=shared --cov-report=html

# Run specific markers
pytest tests/ -m "unit and not slow"
pytest tests/ -m "integration and smoke"
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v

# Stage-specific tests
pytest tests/unit/stages/test_core_stages.py -v
```

---

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── unit/                                # Unit tests
│   ├── test_renamed_stages.py           # Phase 1 renamed stages
│   ├── test_shared_modules.py           # Helper modules
│   └── stages/                          # Stage-specific tests
│       ├── test_core_stages.py
│       └── test_renamed_stage_entry_points.py
├── integration/                         # Integration tests
│   ├── test_standard_media.py           # Media availability
│   ├── test_workflow_integration.py     # Workflow tests
│   └── test_quality_baselines.py        # Quality tests
└── performance/                         # Performance tests
    └── test_benchmarks.py               # Benchmark tests
```

### Test Counts

- **Total Tests:** 170+ tests
- **Unit Tests:** ~105 tests
- **Integration Tests:** ~50 tests
- **Performance Tests:** ~10 tests
- **Execution Time:** <30 seconds (non-slow tests)

---

## Test Markers

### Available Markers

```python
@pytest.mark.unit              # Unit test
@pytest.mark.integration       # Integration test
@pytest.mark.smoke             # Quick smoke test
@pytest.mark.slow              # Slow-running test
@pytest.mark.requires_models   # Requires ML models
@pytest.mark.requires_gpu      # Requires GPU
@pytest.mark.quality_baseline  # Quality baseline test
@pytest.mark.performance       # Performance test
@pytest.mark.stage             # Stage-specific test
@pytest.mark.pipeline          # Full pipeline test
```

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run smoke tests (fast sanity checks)
pytest -m smoke

# Exclude slow tests
pytest -m "not slow"

# Run only integration tests that don't require models
pytest -m "integration and not requires_models"

# Run quality baseline tests
pytest -m quality_baseline
```

---

## Test Fixtures

### Core Fixtures (conftest.py)

```python
project_root            # Path to project root
scripts_dir             # Path to scripts/
shared_dir              # Path to shared/
config_dir              # Path to config/
sample_output_dir       # Temporary output directory
```

### Mock Fixtures

```python
mock_job_dir            # Mock job directory structure
mock_stage_output       # Mock stage output with manifest
mock_config             # Mock configuration dict
mock_audio_file         # Mock WAV file
mock_transcript_json    # Mock transcript JSON
mock_glossary_tsv       # Mock glossary TSV
```

### Test Media Fixtures

```python
sample_media_path       # Sample 1: English technical
sample_media_hinglish   # Sample 2: Hinglish Bollywood
test_media_samples      # Complete metadata for both samples
```

### Quality Baseline Fixtures

```python
quality_baselines           # Quality baseline thresholds
baseline_reference_data     # Reference data for comparison
```

### Performance Fixtures

```python
stage_performance_benchmarks    # Stage performance targets
workflow_performance_benchmarks # Workflow performance targets
```

---

## Writing Tests

### Unit Test Example

```python
import pytest
from pathlib import Path

@pytest.mark.unit
def test_stage_module_imports():
    """Test that stage module imports correctly."""
    from scripts.01_demux import run_stage
    assert callable(run_stage)
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.smoke
def test_prepare_job_creates_structure(sample_media_path: Path):
    """Test that prepare-job creates job structure."""
    # This is a smoke test - checks structure only
    assert sample_media_path.exists()
```

### Quality Baseline Test Example

```python
@pytest.mark.quality_baseline
@pytest.mark.slow
@pytest.mark.skip(reason="Phase 3 - Requires pipeline execution")
def test_sample1_asr_meets_baseline(quality_baselines):
    """Test Sample 1 ASR meets WER baseline."""
    target_wer = quality_baselines["sample1"]["asr_wer_target"]
    # Actual measurement happens in Phase 3
    pytest.skip("Phase 3 - Requires models")
```

### Performance Test Example

```python
@pytest.mark.performance
def test_system_has_sufficient_memory():
    """Test system has sufficient memory."""
    import psutil
    memory = psutil.virtual_memory()
    total_gb = memory.total / 1024 / 1024 / 1024
    assert total_gb >= 4
```

---

## Standard Test Media

### Sample 1: English Technical

**File:** `in/Energy Demand in AI.mp4`  
**Use For:** Transcribe, Translate workflows  
**Language:** English  
**Duration:** 2-5 minutes

**Quality Targets:**
- ASR WER: ≤5%
- Translation BLEU: ≥90%
- Processing Time: <5 minutes

### Sample 2: Hinglish Bollywood

**File:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Use For:** Subtitle, Transcribe, Translate workflows  
**Language:** Hindi/Hinglish  
**Duration:** 1-3 minutes

**Quality Targets:**
- ASR WER: ≤15%
- Subtitle Quality: ≥88%
- Processing Time: <10 minutes (4 languages)

---

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- **Push to main/develop branches**
- **Pull requests**
- **Manual workflow dispatch**

### CI Configuration

File: `.github/workflows/tests.yml`

```yaml
# Tests run on:
- Python 3.11
- Ubuntu latest
- With ffmpeg installed
- With coverage reporting
```

### CI Test Execution

```bash
# Unit tests (always run)
pytest tests/unit -v --cov

# Integration tests (smoke only in CI)
pytest tests/integration -v -m smoke

# Performance tests (system checks only)
pytest tests/performance -v
```

---

## Coverage Reporting

### Generate Coverage Report

```bash
# Terminal output
pytest --cov=scripts --cov=shared --cov-report=term-missing

# HTML report
pytest --cov=scripts --cov=shared --cov-report=html

# JSON report (for CI)
pytest --cov=scripts --cov=shared --cov-report=json
```

### View Coverage

```bash
# Open HTML report
open test-results/coverage/index.html

# Check coverage JSON
cat test-results/coverage.json | jq '.totals.percent_covered'
```

### Coverage Targets

- **Overall:** ≥80%
- **Critical Modules:** ≥90%
- **Helper Modules:** ≥85%
- **Stage Scripts:** ≥70%

---

## Test Execution Strategies

### Development Workflow

```bash
# 1. Quick sanity check (smoke tests)
pytest -m smoke --tb=short

# 2. Run affected tests
pytest tests/unit/test_renamed_stages.py -v

# 3. Run full unit suite
pytest tests/unit/ -v

# 4. Run integration tests (if needed)
pytest tests/integration/ -m "not slow"
```

### Pre-Commit

```bash
# Run fast tests before commit
pytest tests/unit/ -m "not slow" --tb=short -q

# Or use the compliance validator
python scripts/validate-compliance.py --staged
```

### Pre-Push

```bash
# Run all non-slow tests
pytest tests/ -m "not slow" -v

# Check coverage
pytest --cov=scripts --cov=shared --cov-report=term
```

### Release Testing

```bash
# Run full test suite including slow tests
pytest tests/ -v

# Run quality baseline tests
pytest -m quality_baseline -v

# Run performance tests
pytest -m performance -v

# Generate full coverage report
pytest --cov=scripts --cov=shared --cov-report=html
```

---

## Troubleshooting

### Common Issues

**Issue:** Tests fail with import errors

```bash
# Solution: Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

**Issue:** Slow test execution

```bash
# Solution: Exclude slow tests
pytest -m "not slow" -v

# Or run specific fast tests
pytest tests/unit/ -v
```

**Issue:** Missing test media

```bash
# Solution: Check that test media files exist
ls -lh "in/Energy Demand in AI.mp4"
ls -lh "in/test_clips/jaane_tu_test_clip.mp4"
```

**Issue:** Permission errors

```bash
# Solution: Ensure output directories are writable
chmod -R u+w test-results/
chmod -R u+w out/
```

---

## Test Maintenance

### Adding New Tests

1. **Choose appropriate directory:**
   - `tests/unit/` for unit tests
   - `tests/integration/` for integration tests
   - `tests/performance/` for performance tests

2. **Use appropriate markers:**
   - Add `@pytest.mark.unit` or `@pytest.mark.integration`
   - Add `@pytest.mark.slow` if test takes >5 seconds
   - Add `@pytest.mark.skip()` with reason if not yet implemented

3. **Write comprehensive docstrings:**
   ```python
   def test_feature():
       """
       Test that feature works correctly.
       
       Expected:
           - Feature should do X
           - Feature should not do Y
       """
   ```

4. **Use fixtures when possible:**
   - Reuse existing fixtures from `conftest.py`
   - Create new fixtures if needed

### Updating Baselines

When quality improves or models change:

1. Update `docs/QUALITY_BASELINES.md`
2. Update fixture values in `conftest.py`
3. Document changes in baseline history
4. Run baseline tests to verify

### Deprecating Tests

If a test becomes obsolete:

1. Mark with `@pytest.mark.skip(reason="Deprecated: [reason]")`
2. Document in test file header
3. Remove after 1-2 releases

---

## Test Development Guidelines

### Test Naming

```python
# Good: Descriptive, clear intent
def test_demux_creates_audio_file()
def test_whisperx_handles_empty_audio()
def test_translation_preserves_glossary_terms()

# Bad: Vague, unclear
def test_demux()
def test_works()
def test_feature()
```

### Test Structure

```python
def test_feature():
    """Clear docstring explaining what is tested."""
    # 1. Setup (Arrange)
    input_data = create_test_data()
    
    # 2. Execute (Act)
    result = function_under_test(input_data)
    
    # 3. Verify (Assert)
    assert result.success is True
    assert result.value == expected_value
```

### Test Independence

- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order
- Clean up resources in teardown

---

## Performance Testing

### Running Performance Tests

```bash
# All performance tests
pytest tests/performance/ -v

# System resource tests only
pytest tests/performance/ -k "system" -v

# Benchmark tests only
pytest tests/performance/ -k "benchmark" -v
```

### Performance Benchmarks

See `docs/QUALITY_BASELINES.md` for complete performance targets.

---

## Quality Baseline Testing

### Running Quality Tests

```bash
# All quality baseline tests
pytest -m quality_baseline -v

# Infrastructure tests only (no execution required)
pytest tests/integration/test_quality_baselines.py::TestBaselineInfrastructure -v

# Actual quality tests (Phase 3, requires models)
pytest -m "quality_baseline and requires_models" -v
```

### Quality Metrics

- **ASR Quality:** Word Error Rate (WER)
- **Translation Quality:** BLEU score
- **Subtitle Quality:** Timing, CPS, line length
- **Context Awareness:** Glossary application, coherence

---

## Additional Resources

- **Developer Standards:** `docs/developer/DEVELOPER_STANDARDS.md`
- **Code Examples:** `docs/CODE_EXAMPLES.md`
- **Quality Baselines:** `docs/QUALITY_BASELINES.md`
- **System Status:** `SYSTEM_STATUS_REPORT.md`

---

## Getting Help

**Common Commands:**
```bash
# List all available markers
pytest --markers

# List all available fixtures
pytest --fixtures

# Get help on pytest options
pytest --help
```

**Test Reports:**
- JUnit XML: `test-results/junit.xml`
- Coverage HTML: `test-results/coverage/index.html`
- Coverage JSON: `test-results/coverage.json`

---

**END OF TESTING GUIDE**
