# Developer Quick Reference

**Quick reference card for common development tasks**

---

## 🚀 Quick Start

```bash
# Setup
./bootstrap.sh

# Test job
./prepare-job.sh --media in/test.mp4 --workflow transcribe --source-lang hi --debug
./run-pipeline.sh -j <job-id>

# Check logs
tail -f out/<date>/<user>/<job>/logs/*.log
```

---

## 📝 Commit Messages

```bash
fix:      Bug fix
feat:     New feature
docs:     Documentation
refactor: Code restructure
test:     Tests
chore:    Build/tooling
```

**Example:**
```bash
git commit -m "fix: enable source separation by default"
```

---

## 🎯 Code Standards

### Naming
```python
MAX_RETRIES = 3              # Constants: UPPER_SNAKE_CASE
class AudioProcessor:        # Classes: PascalCase
def process_audio():         # Functions: snake_case
user_id = 1                  # Variables: snake_case
```

### Type Hints (Always)
```python
def process(input: Path, quality: str = "balanced") -> Optional[Path]:
    pass
```

### Docstrings (Always)
```python
def process_audio(input_path: Path) -> Optional[Path]:
    """
    Process audio with source separation.
    
    Args:
        input_path: Path to input audio file
    
    Returns:
        Path to processed audio, or None if failed
    """
    pass
```

---

## 📊 Logging

### Initialization
```python
# For stages
from shared.stage_utils import get_stage_logger
logger = get_stage_logger("my_stage", stage_io=stage_io)

# For classes
from shared.logger import PipelineLogger
logger = PipelineLogger(module_name="my_module", log_level="INFO")
```

### Usage
```python
logger.info("Starting process...")              # General info
logger.debug(f"Config: {config}")               # Debug details
logger.warning(f"Retrying: {attempt}/{max}")    # Warnings
logger.error(f"Failed: {error}")                # Errors
```

### Format
`[2025-11-21 12:00:00] [module_name] [INFO] Message`

---

## ⚙️ Configuration

**CRITICAL RULES:**
- ❌ NEVER use hardcoded values
- ❌ NEVER read os.environ directly  
- ✅ ALWAYS define in config/.env.pipeline
- ✅ ALWAYS use Config class

```python
# ❌ WRONG - Hardcoded
quality = "balanced"

# ❌ WRONG - Direct os.environ
quality = os.environ.get('QUALITY', 'balanced')

# ✅ CORRECT - Use Config class
from shared.config import Config
config = Config(PROJECT_ROOT)
quality = config.get('SOURCE_SEPARATION_QUALITY', 'balanced')
batch_size = int(config.get('BATCH_SIZE', 8))
enabled = config.get('FEATURE_ENABLED', 'false').lower() == 'true'
```

---

## 🏗️ Stage Pattern

```python
#!/usr/bin/env python3
"""Stage: My Stage"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger

def main():
    # 1. Initialize
    stage_io = StageIO("my_stage")
    logger = get_stage_logger("my_stage", stage_io=stage_io)
    
    # 2. Log start
    logger.info("=" * 60)
    logger.info("MY STAGE")
    logger.info("=" * 60)
    
    # 3. Check if enabled
    enabled = os.environ.get('MY_STAGE_ENABLED', 'false').lower() == 'true'
    if not enabled:
        logger.info("Stage disabled (skipping)")
        return 0
    
    # 4. Get input
    input_file = stage_io.get_input_path("data.json", from_stage="previous")
    if not input_file.exists():
        logger.error(f"Input not found: {input_file}")
        return 1
    
    # 5. Process
    try:
        output = process(input_file, logger)
        if not output:
            logger.error("Processing failed")
            return 1
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        return 1
    
    # 6. Save output
    stage_io.save_output("output.json", output)
    
    # 7. Log completion
    logger.info("✓ Stage completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## 🚨 Error Handling

```python
# Specific exceptions
try:
    result = process()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return None
except subprocess.TimeoutExpired:
    logger.error("Processing timed out")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    if debug:
        logger.error(f"Traceback: {traceback.format_exc()}")
    return None
```

---

## 🔧 Common Tasks

### Get input from previous stage
```python
stage_io = StageIO("my_stage")
input_file = stage_io.get_input_path("audio.wav", from_stage="demux")
```

### Run in specific environment
```python
result = self._run_in_environment(
    "asr",
    [sys.executable, str(script_path)],
    env=env
)
```

### Check environment installed
```python
env_manager = EnvironmentManager(PROJECT_ROOT)
if env_manager.is_environment_installed("whisperx"):
    # Use WhisperX
    pass
```

### Progress indication
```python
logger.info(f"Processing {total} items...")
for i, item in enumerate(items, 1):
    process(item)
    if i % 100 == 0:
        logger.info(f"Progress: {i}/{total} ({i*100//total}%)")
```

---

## ✅ Pre-Commit Checklist

```
□ Read PROCESS.md
□ Made minimal changes
□ Used proper logging (with module name)
□ Config via Config class (NO os.environ!)
□ NO hardcoded values in code
□ All parameters in config/.env.pipeline
□ Error handling added
□ Tested default & edge cases
□ Documentation updated IMMEDIATELY
□ Commit message formatted
□ No print() statements
□ Backward compatible
□ Virtual environment isolation maintained
```

---

## 📚 Essential Docs

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Complete guide
- **[PROCESS.md](PROCESS.md)** - Development process
- **[Architecture](technical/architecture.md)** - System design
- **[INDEX.md](INDEX.md)** - All documentation

---

## 🆘 Troubleshooting

```bash
# Module not found
sys.path.insert(0, str(PROJECT_ROOT))

# Check environment
./health-check.sh

# Enable debug
./prepare-job.sh --debug ...

# Watch logs
tail -f out/<date>/<user>/<job>/logs/*.log

# Check job config
cat out/<date>/<user>/<job>/job.json | jq .
```

---

**For full details, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**
