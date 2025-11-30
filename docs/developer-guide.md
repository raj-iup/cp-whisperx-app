# Developer Guide

**CP-WhisperX-App Development Guide for Apple Silicon M1 Pro**

---

## Overview

This guide provides comprehensive instructions for developers working on the CP-WhisperX pipeline. It covers development environment setup, code standards, project structure, and testing guidelines specifically optimized for Apple Silicon.

---

## Development Environment Setup

### Prerequisites

- **Hardware**: Apple Silicon Mac (M1/M1 Pro/M2/M3)
- **OS**: macOS 13.0 (Ventura) or later
- **Python**: 3.11+
- **FFmpeg**: 6.0+ with hardware acceleration support

### Initial Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app

# 2. Run bootstrap to set up the development environment
./scripts/bootstrap.sh

# 3. Activate the virtual environment
source .bollyenv/bin/activate

# 4. Verify MPS (Metal Performance Shaders) support
python3 -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

### Virtual Environment

The project uses a Python virtual environment (`.bollyenv/`) managed by `bootstrap.sh`:

```bash
# Create new environment (if needed)
python3 -m venv .bollyenv
source .bollyenv/bin/activate
pip install -r requirements-macos.txt
```

### Required Dependencies

Install dependencies based on your platform:

```bash
# macOS (Apple Silicon) - recommended
pip install -r requirements-macos.txt

# Cross-platform base requirements
pip install -r requirements.txt

# Optional features
pip install -r requirements-optional.txt
```

---

## Project Structure

```
cp-whisperx-app/
├── scripts/                 # Core pipeline scripts
│   ├── pipeline.py         # Main orchestrator
│   ├── whisperx_integration.py  # WhisperX ASR integration
│   ├── diarization.py      # Speaker diarization
│   ├── subtitle_gen.py     # Subtitle generation
│   └── ...                 # Other pipeline stages
├── shared/                  # Shared utilities and modules
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging utilities
│   └── ...                 # Shared helpers
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest configuration
│   ├── test_*.py           # Test modules
│   └── __init__.py
├── config/                  # Configuration files
│   ├── .env.example        # Environment template
│   └── ...                 # Config templates
├── docs/                    # Documentation
│   ├── INDEX.md            # Documentation index
│   ├── developer-guide.md  # This file
│   ├── user-guide/         # User documentation
│   ├── technical/          # Technical documentation
│   └── archive/            # Historical documentation
├── glossary/               # Glossary files for bias terms
├── in/                     # Input video files
├── out/                    # Output directory
└── tools/                  # Utility tools
```

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Core pipeline processing scripts |
| `shared/` | Shared modules, utilities, and configuration |
| `tests/` | Test suite with pytest |
| `config/` | Configuration files and templates |
| `docs/` | Project documentation |
| `glossary/` | Bias term glossaries |

---

## Code Standards and Conventions

### Python Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use [PEP 257](https://peps.python.org/pep-0257/) docstring conventions
- Maximum line length: 100 characters
- Use type hints for function signatures

### Naming Conventions

```python
# Variables and functions: snake_case
def process_audio_segment(audio_path: Path) -> dict:
    segment_duration = 30.0
    
# Classes: PascalCase
class AudioProcessor:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_SAMPLE_RATE = 16000
MAX_SEGMENT_LENGTH = 30.0
```

### Module Structure

```python
#!/usr/bin/env python3
"""
Module docstring describing the purpose.

This module provides functionality for...
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict

# Add project root to path if needed
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Internal imports
from shared.config import PipelineConfig
from shared.logger import PipelineLogger


class MyClass:
    """Class docstring."""
    
    def __init__(self, config: PipelineConfig):
        """Initialize with configuration."""
        self.config = config
    
    def process(self, data: dict) -> dict:
        """Process the data and return results."""
        # Implementation
        pass


def main() -> int:
    """Main entry point."""
    # Implementation
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Error Handling

```python
# Use specific exceptions
try:
    result = process_audio(audio_path)
except FileNotFoundError:
    logger.error(f"Audio file not found: {audio_path}")
    raise
except RuntimeError as e:
    logger.error(f"Processing failed: {e}")
    raise

# Use context managers for resources
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
```

### Logging

Use the project's logger for consistent output:

```python
from shared.logger import PipelineLogger

logger = PipelineLogger(stage_name="my_stage", output_base=output_dir)
logger.info("Processing started")
logger.debug("Detailed debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

---

## Hardware-Specific Notes (Apple Silicon)

### MPS Backend (Metal Performance Shaders)

Apple Silicon Macs use MPS for GPU acceleration:

```python
import torch

# Check MPS availability
if torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

# Move tensors to MPS
tensor = tensor.to(device)
model = model.to(device)
```

### Memory Management

Apple Silicon has unified memory architecture. Follow these best practices:

```python
# Clear GPU cache after heavy operations
import torch
if torch.backends.mps.is_available():
    torch.mps.empty_cache()

# Use smaller batch sizes to prevent OOM
BATCH_SIZE = 8  # Adjust based on model and memory

# Enable memory-efficient attention when available
if hasattr(model, 'enable_attention_slicing'):
    model.enable_attention_slicing()
```

### Device Selection

Use the project's device selector:

```python
from scripts.device_selector import get_device

# Automatic device selection
device = get_device()  # Returns 'mps', 'cuda', or 'cpu'

# Or use configuration
from shared.config import PipelineConfig
config = PipelineConfig()
device = config.whisperx_device  # 'auto', 'mps', 'cpu', etc.
```

### MLX Integration

For optimal performance on Apple Silicon, the project uses MLX-Whisper:

```python
# MLX is automatically used when available
# Backend selection is handled by whisperx_integration.py

# To verify MLX is being used:
# Check logs for "Backend: Apple MLX (Metal)"
```

### Performance Tips

1. **Batch Processing**: Process audio in chunks to manage memory
2. **Model Loading**: Load models once and reuse
3. **Cache Management**: Clear MPS cache between large operations
4. **Memory Monitoring**: Watch Activity Monitor during development

```bash
# Monitor GPU usage
sudo powermetrics --samplers gpu_power -i 1000

# Check memory pressure
memory_pressure
```

---

## Testing Guidelines

### Test Structure

Tests are located in the `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_enhancements.py     # Enhancement tests
├── test_glossary_system.py  # Glossary system tests
├── test_indictrans2.py      # IndicTrans2 tests
├── test_lyrics_enhancement.py
├── test_musicbrainz.py
└── test_subtitle_enhancement.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_glossary_system.py

# Run with verbose output
pytest -v tests/

# Run with coverage
pytest --cov=scripts --cov=shared tests/
```

### Writing Tests

```python
#!/usr/bin/env python3
"""Test module for feature X."""

import pytest
from pathlib import Path

# Fixtures from conftest.py are automatically available
def test_feature_basic(project_root: Path):
    """Test basic feature functionality."""
    assert project_root.exists()

def test_feature_with_mock(mocker, sample_output_dir: Path):
    """Test feature with mocking."""
    mock_processor = mocker.patch('scripts.processor.process')
    mock_processor.return_value = {'status': 'success'}
    
    # Test implementation
    result = process_data()
    assert result['status'] == 'success'

@pytest.mark.parametrize("input,expected", [
    ("test1", True),
    ("test2", False),
])
def test_parametrized(input, expected):
    """Test with multiple inputs."""
    result = check_input(input)
    assert result == expected
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

@pytest.fixture
def sample_output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory for tests."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
```

---

## Contributing Guidelines

### Branch Naming

```
feature/   - New features (feature/add-language-support)
fix/       - Bug fixes (fix/audio-processing-error)
docs/      - Documentation updates (docs/update-readme)
refactor/  - Code refactoring (refactor/pipeline-stages)
test/      - Test additions/updates (test/add-unit-tests)
```

### Commit Messages

Follow conventional commits:

```
feat: add support for new language
fix: resolve audio processing crash on long files
docs: update developer guide with MPS info
refactor: simplify pipeline stage execution
test: add unit tests for glossary system
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commits
3. Run tests and ensure they pass
4. Update documentation if needed
5. Submit PR with clear description
6. Address review feedback

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced
- [ ] Memory management considered for Apple Silicon
- [ ] Error handling is appropriate

---

## Debugging

### Debug Mode

Enable detailed logging:

```bash
# Set debug mode in environment
export PIPELINE_DEBUG=true

# Or use bootstrap debug mode
./scripts/bootstrap.sh --debug
```

### Common Issues

#### MPS Out of Memory

```python
# Solution: Clear cache and reduce batch size
torch.mps.empty_cache()
# Reduce BATCH_SIZE in processing code
```

#### Import Errors

```python
# Ensure project root is in path
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

#### Model Loading Issues

```bash
# Check model status
./check-models.sh

# Re-download models
./scripts/bootstrap.sh --refresh-models
```

---

## Documentation

### Documentation Structure

```
docs/
├── INDEX.md                 # Main navigation
├── developer-guide.md       # This file
├── user-guide/              # End-user documentation
│   ├── QUICKSTART.md
│   └── CONFIGURATION.md
├── technical/               # Technical documentation
│   ├── ARCHITECTURE.md
│   └── PIPELINE_*.md
└── archive/                 # Historical documentation
    ├── phase-completion/
    └── refactor-history/
```

### Writing Documentation

- Use clear, concise language
- Include code examples where helpful
- Keep documentation up to date with code changes
- Use relative links between documents

---

## Additional Resources

- [Project README](../README.md) - Project overview and quick start
- [Documentation Index](INDEX.md) - Complete documentation navigation
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Apple Silicon Quick Reference](user-guide/APPLE_SILICON_QUICK_REF.md) - MPS/GPU optimization

---

**Last Updated:** November 2025  
**Maintainers:** CP-WhisperX Team
