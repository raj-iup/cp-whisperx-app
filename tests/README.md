# Testing Infrastructure

**Phase 2: Testing Infrastructure** - Comprehensive test suite for CP-WhisperX-App

## Overview

This testing infrastructure provides comprehensive test coverage for the pipeline, including:
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Tests for complete workflows and stage interactions
- **Stage Tests**: Specific tests for each pipeline stage
- **Utilities**: Helpers for test creation, execution, and validation

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements/requirements-test.txt
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m smoke         # Smoke tests only
pytest -m stage         # Stage-specific tests
```

### Run Tests by Directory

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Stage tests
pytest tests/stages -v
```

## Test Organization

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── pytest.ini               # Pytest settings
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_stage_utils.py
│   ├── test_config_loader.py
│   └── ...
├── integration/             # Integration tests (slower, may use external services)
│   ├── test_pipeline_end_to_end.py
│   └── ...
├── stages/                  # Stage-specific tests
│   ├── test_tmdb_stage.py
│   └── ...
└── utils/                   # Test utilities and helpers
    ├── test_helpers.py
    └── ...
```

## Test Markers

Tests are organized using pytest markers:

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Fast unit tests | `@pytest.mark.unit` |
| `integration` | Integration tests | `@pytest.mark.integration` |
| `slow` | Slow tests (model loading, GPU) | `@pytest.mark.slow` |
| `requires_gpu` | Tests requiring GPU | `@pytest.mark.requires_gpu` |
| `requires_models` | Tests requiring ML models | `@pytest.mark.requires_models` |
| `requires_network` | Tests requiring network | `@pytest.mark.requires_network` |
| `stage` | Stage-specific tests | `@pytest.mark.stage` |
| `smoke` | Quick smoke tests | `@pytest.mark.smoke` |

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run smoke tests (quick validation)
pytest -m smoke

# Run tests that don't require GPU
pytest -m "not requires_gpu"
```

## Test Utilities

### TestJobBuilder

Create test job directories with proper structure:

```python
from tests.utils.test_helpers import TestJobBuilder

builder = TestJobBuilder()
job_dir = builder.create_job(workflow="transcribe")
builder.add_sample_audio(job_dir)
```

### Assertion Helpers

Common assertions for testing stages:

```python
from tests.utils.test_helpers import (
    assert_stage_completed,
    assert_logs_exist,
    assert_manifest_valid,
    assert_stage_output_tracked
)

# Assert stage completed successfully
assert_stage_completed(job_dir, "01_demux")

# Assert stage logs exist
assert_logs_exist(job_dir, "01_demux")

# Assert manifest is valid
assert_manifest_valid(manifest_path)

# Assert outputs are tracked
assert_stage_output_tracked(job_dir, "01_demux", ["audio.wav"])
```

### Mock Models

Mock expensive model operations for testing:

```python
from tests.utils.test_helpers import mock_whisperx_model, mock_indictrans2_model

# Mock WhisperX model
model = mock_whisperx_model()
result = model.transcribe("audio.wav")

# Mock IndicTrans2 model
model = mock_indictrans2_model()
translation = model.translate("text", "en", "hi")
```

## Coverage Reports

### Generate Coverage Report

```bash
# HTML report (test-results/coverage/index.html)
pytest --cov --cov-report=html

# Terminal report
pytest --cov --cov-report=term-missing

# JSON report
pytest --cov --cov-report=json:test-results/coverage.json
```

### View Coverage

```bash
# Open HTML report
open test-results/coverage/index.html
```

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

See `.github/workflows/tests.yml` for CI/CD configuration.

### CI/CD Test Flow

1. **Unit Tests**: Fast tests without external dependencies
2. **Integration Tests**: Smoke tests only (full integration in Phase 3)
3. **Code Quality**: Compliance validator, linting, formatting
4. **Coverage Report**: Uploaded to Codecov and PR comments

## Writing New Tests

### Unit Test Template

```python
#!/usr/bin/env python3
"""Unit tests for [component]."""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.mark.unit
class TestMyComponent:
    """Unit tests for MyComponent."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Test implementation
        assert True
```

### Integration Test Template

```python
#!/usr/bin/env python3
"""Integration tests for [workflow]."""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.utils.test_helpers import TestJobBuilder

@pytest.mark.integration
class TestMyWorkflow:
    """Integration tests for workflow."""
    
    @pytest.fixture
    def job_builder(self, tmp_path):
        """Create job builder."""
        builder = TestJobBuilder(base_dir=tmp_path)
        yield builder
        builder.cleanup()
    
    def test_workflow(self, job_builder):
        """Test workflow end-to-end."""
        job_dir = job_builder.create_job()
        # Test implementation
        assert True
```

## Test Development Guidelines

### Do's ✅

- Use markers to categorize tests
- Mock expensive operations (model loading, API calls)
- Use test fixtures for setup/teardown
- Write descriptive test names
- Test both success and failure cases
- Clean up temporary files after tests
- Use assertion helpers from test_helpers

### Don'ts ❌

- Don't load ML models in unit tests
- Don't make network calls without `requires_network` marker
- Don't use GPU without `requires_gpu` marker
- Don't leave temporary files after tests
- Don't skip tests without good reason
- Don't test implementation details

## Test Coverage Goals

| Phase | Coverage Target | Status |
|-------|----------------|--------|
| Phase 2 (Current) | 60%+ | 🟡 In Progress |
| Phase 3 | 75%+ | ⏳ Planned |
| Phase 4 | 85%+ | ⏳ Planned |
| Phase 5 | 90%+ | ⏳ Planned |

## Troubleshooting

### Tests Fail to Import Modules

```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Coverage Report Not Generated

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with explicit coverage options
pytest --cov=scripts --cov=shared --cov-report=html
```

### Tests Run Too Slowly

```bash
# Run only fast tests
pytest -m "not slow"

# Run tests in parallel
pip install pytest-xdist
pytest -n auto
```

### Test Dependencies Missing

```bash
# Install all test dependencies
pip install -r requirements/requirements-test.txt

# Verify installation
pip list | grep pytest
```

## Phase 2 Deliverables

- [x] pytest configuration (pytest.ini)
- [x] Test requirements (requirements-test.txt)
- [x] Test utilities (test_helpers.py)
- [x] Unit tests for shared utilities
- [x] Integration test framework
- [x] Stage test templates
- [x] CI/CD workflow (.github/workflows/tests.yml)
- [x] Mock model utilities
- [x] Coverage reporting
- [x] Documentation (this file)

## Next Steps: Phase 3

Phase 3 will focus on converting existing stages to use the StageIO pattern and adding comprehensive tests:

1. Convert demux stage → Add tests
2. Convert ASR stage → Add tests
3. Convert translation stage → Add tests
4. Convert subtitle_gen stage → Add tests
5. Convert mux stage → Add tests
6. Enable full integration tests

See `docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md` for details.

## Resources

- **Roadmap**: `docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md`
- **Developer Standards**: `docs/developer/DEVELOPER_STANDARDS.md`
- **Code Examples**: `docs/CODE_EXAMPLES.md`
- **Pytest Documentation**: https://docs.pytest.org/
- **Coverage.py Documentation**: https://coverage.readthedocs.io/

---

**Version**: Phase 2 Complete  
**Date**: 2025-12-03  
**Status**: ✅ Ready for Use
