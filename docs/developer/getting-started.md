# Developer Guide

Contribution guidelines and development standards for the WhisperX Speech Processing Pipeline.

## Overview

This guide covers:
- Development setup and workflow
- Code standards and patterns
- Testing requirements
- Contribution process

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tools
- IDE with Python support (VSCode, PyCharm recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd cp-whisperx-app

# Run bootstrap
./bootstrap.sh

# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -r requirements/dev.txt  # if available
```

### Project Structure

```
cp-whisperx-app/
├── scripts/                    # Main pipeline scripts
│   ├── transcribe/            # Transcription stage
│   │   ├── transcribe.py     # Main transcription
│   │   └── lyrics_detection.py
│   ├── translate/             # Translation stage
│   │   ├── translate.py      # Main translation
│   │   ├── indictrans2.py    # Indian languages
│   │   └── retranslate.py    # Retranslation
│   ├── subtitles/             # Subtitle generation
│   │   └── subtitles.py      # SRT/VTT generation
│   └── shared/                # Shared utilities
│       ├── logger.py         # Centralized logging
│       ├── config.py         # Configuration management
│       └── utils.py          # Common utilities
├── config/                    # Configuration files
├── glossary/                  # Glossary definitions
├── tests/                     # Test suite
├── docs/                      # Documentation
└── tools/                     # Development tools
```

## Code Standards

### Python Style

**Follow PEP 8** with these specifics:

```python
# Line length: 100 characters (not 80)
# Use type hints
def process_audio(file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Process audio file with configuration.
    
    Args:
        file_path: Path to audio file
        config: Configuration dictionary
        
    Returns:
        Dictionary with processing results
    """
    pass

# Use descriptive variable names
transcription_result = transcribe_audio(audio_path)  # Good
tr = transcribe(ap)  # Bad

# Constants in UPPER_CASE
DEFAULT_BEAM_SIZE = 5
MAX_RETRY_ATTEMPTS = 3
```

### Logging Standards

**Always use the shared logger**:

```python
from shared.logger import get_logger

logger = get_logger(__name__)

# Log levels
logger.debug("Detailed debug information")
logger.info("General informational messages")
logger.warning("Warning messages for recoverable issues")
logger.error("Error messages for failures")
logger.critical("Critical failures requiring immediate attention")

# Structured logging
logger.info(f"Processing file: {file_path}")
logger.info(f"Configuration: beam_size={beam_size}, best_of={best_of}")
```

### Error Handling

**Comprehensive error handling**:

```python
try:
    result = process_audio(file_path)
except FileNotFoundError as e:
    logger.error(f"Audio file not found: {file_path}")
    raise
except TranscriptionError as e:
    logger.error(f"Transcription failed: {e}")
    # Handle gracefully or re-raise
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
finally:
    # Cleanup resources
    cleanup_temp_files()
```

### Configuration Management

**Use configuration files, not hardcoded values**:

```python
from shared.config import load_config

# Load configuration
config = load_config("config/pipeline.conf")
job_config = load_config(f"config/job_{job_name}.conf")

# Access values with defaults
beam_size = config.get("beam_size", 5)
target_lang = job_config.get("target_lang", "en")

# Never hardcode
beam_size = 5  # Bad
```

### Documentation Standards

**Document all public functions and classes**:

```python
def transcribe_audio(
    audio_path: str,
    model_name: str = "large-v3",
    beam_size: int = 5,
    compute_type: str = "float16"
) -> Dict[str, Any]:
    """Transcribe audio file using WhisperX.
    
    Performs speech-to-text transcription with forced alignment
    and optional diarization.
    
    Args:
        audio_path: Path to audio file
        model_name: WhisperX model to use (default: large-v3)
        beam_size: Beam search width (default: 5)
        compute_type: Computation precision (default: float16)
        
    Returns:
        Dictionary containing:
            - segments: List of transcription segments
            - word_segments: Word-level alignments
            - language: Detected language
            - metadata: Processing metadata
            
    Raises:
        FileNotFoundError: If audio file doesn't exist
        TranscriptionError: If transcription fails
        
    Example:
        >>> result = transcribe_audio("audio.mp3")
        >>> print(result['language'])
        'en'
    """
    pass
```

## Development Workflow

### Making Changes

1. **Create a branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** following code standards

3. **Test locally**:
   ```bash
   ./test_phase1.sh
   ```

4. **Commit with clear messages**:
   ```bash
   git commit -m "Add: Feature description"
   # or
   git commit -m "Fix: Bug description"
   # or
   git commit -m "Update: Documentation for X"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   ```

### Commit Message Format

Use prefixes for clarity:

- `Add:` New features or functionality
- `Fix:` Bug fixes
- `Update:` Updates to existing features
- `Refactor:` Code refactoring
- `Docs:` Documentation changes
- `Test:` Test additions or modifications
- `Style:` Code style changes (formatting, etc.)

Examples:
```
Add: Support for Urdu language in IndicTrans2
Fix: Memory leak in transcription loop
Update: Improve glossary matching algorithm
Docs: Add troubleshooting guide for MLX
```

## Testing

### Running Tests

```bash
# Run full test suite
./test_phase1.sh

# Run specific test
./test-glossary-simple.sh
./test-glossary-quickstart.sh
```

### Writing Tests

**Create test scripts** in `tests/` directory:

```python
#!/usr/bin/env python3
"""Test transcription functionality."""

import sys
from pathlib import Path
from scripts.transcribe.transcribe import transcribe_audio

def test_basic_transcription():
    """Test basic transcription."""
    audio_path = "tests/fixtures/test_audio.mp3"
    result = transcribe_audio(audio_path)
    
    assert result is not None
    assert "segments" in result
    assert len(result["segments"]) > 0
    print("✓ Basic transcription test passed")

def test_language_detection():
    """Test language detection."""
    audio_path = "tests/fixtures/hindi_audio.mp3"
    result = transcribe_audio(audio_path)
    
    assert result["language"] == "hi"
    print("✓ Language detection test passed")

if __name__ == "__main__":
    test_basic_transcription()
    test_language_detection()
    print("\nAll tests passed!")
```

### Test Data

- Store test fixtures in `tests/fixtures/`
- Use small audio files (< 1MB)
- Include multiple languages
- Document test data sources

## Pipeline Development

### Adding New Features

#### New Pipeline Stage

1. Create stage directory: `scripts/new_stage/`
2. Implement main script: `scripts/new_stage/process.py`
3. Add logging and error handling
4. Update configuration templates
5. Update `run-pipeline.sh` to include stage
6. Document in `docs/technical/pipeline.md`

#### New Translation Engine

1. Create module: `scripts/translate/new_engine.py`
2. Implement standard interface:
   ```python
   def translate(text: str, source_lang: str, target_lang: str) -> str:
       """Translate text using new engine."""
       pass
   ```
3. Add to translation fallback chain
4. Update language support documentation

#### New Model Support

1. Add model loading logic
2. Update environment detection
3. Test on all platforms (MLX/CUDA/CPU)
4. Document requirements and performance

### Modifying Existing Features

1. **Understand current behavior**: Read code and tests
2. **Check dependencies**: What else depends on this?
3. **Update tests**: Modify or add tests first
4. **Make minimal changes**: Surgical modifications only
5. **Test thoroughly**: Run full test suite
6. **Update docs**: Keep documentation in sync

## Code Review Guidelines

### For Authors

- Keep PRs focused and small
- Write clear descriptions
- Include tests
- Update documentation
- Run tests before submitting

### For Reviewers

Check for:
- Code follows standards
- Adequate error handling
- Proper logging
- Tests included
- Documentation updated
- No hardcoded values
- Performance implications considered

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

# Profile function
profiler = cProfile.Profile()
profiler.enable()

result = expensive_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Memory Optimization

```python
# Use generators for large datasets
def process_segments(segments):
    for segment in segments:
        yield process_segment(segment)

# Instead of
def process_segments(segments):
    return [process_segment(s) for s in segments]  # Loads all in memory
```

### Best Practices

- Profile before optimizing
- Optimize bottlenecks, not everything
- Consider memory vs. speed tradeoffs
- Document performance characteristics
- Test on target hardware

## Documentation Standards

### When to Update Docs

Update documentation when:
- Adding new features
- Changing existing behavior
- Fixing bugs that affect usage
- Updating configuration options
- Changing CLI interfaces

### Documentation Structure

Follow the established structure:
- **User guides**: How to use features
- **Technical docs**: How things work
- **Reference**: API documentation
- **Developer docs**: How to contribute

### Writing Style

- Clear and concise
- Use examples liberally
- Test all code examples
- Keep up to date
- Link between related docs

## Compliance and Standards

See [Developer Standards Compliance](DEVELOPER_STANDARDS_COMPLIANCE.md) for detailed compliance requirements.

## Getting Help

- **Documentation**: [docs/INDEX.md](INDEX.md)
- **Technical Details**: [docs/technical/](technical/README.md)
- **Architecture**: [docs/technical/architecture.md](technical/architecture.md)

## Resources

- **Python Style Guide**: [PEP 8](https://pep8.org/)
- **Type Hints**: [PEP 484](https://www.python.org/dev/peps/pep-0484/)
- **Docstrings**: [PEP 257](https://www.python.org/dev/peps/pep-0257/)

---

**Navigation**: [Home](../README.md) | [Documentation Index](INDEX.md) | [Standards](DEVELOPER_STANDARDS_COMPLIANCE.md)
