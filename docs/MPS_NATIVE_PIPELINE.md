# MPS-Based Native Pipeline Design

**Goal**: Mac-optimized pipeline without Docker, using MPS acceleration

---

## Architecture Overview

### Stage Isolation Strategy
- Each stage has its own Python virtual environment
- Location: `.venvs/<stage>/`
- No dependency conflicts between stages
- Lightweight compared to Docker containers

### MPS vs CPU Decision Matrix

| Stage | MPS Benefit | Decision | Reason |
|-------|-------------|----------|--------|
| demux | None | **CPU** | FFmpeg CLI tool, not Python |
| tmdb | None | **CPU** | API calls, no compute |
| pre-ner | High | **MPS→CPU** | Transformer models benefit from GPU |
| silero-vad | High | **MPS→CPU** | Audio ML model, GPU accelerated |
| pyannote-vad | High | **MPS→CPU** | Audio ML model, GPU accelerated |
| diarization | High | **MPS→CPU** | Speaker clustering, GPU accelerated |
| asr | Very High | **MPS→CPU** | WhisperX - largest benefit from GPU |
| post-ner | High | **MPS→CPU** | Transformer models benefit from GPU |
| subtitle-gen | None | **CPU** | Text processing only |
| mux | None | **CPU** | FFmpeg CLI tool, not Python |

**Priority for MPS**: asr > diarization > silero-vad > pyannote-vad > pre-ner > post-ner

---

## Directory Structure

```
cp-whisperx-app/
├── native/                      # New native pipeline
│   ├── venvs/                   # Virtual environments
│   │   ├── demux/
│   │   ├── tmdb/
│   │   ├── pre-ner/
│   │   ├── silero-vad/
│   │   ├── pyannote-vad/
│   │   ├── diarization/
│   │   ├── asr/
│   │   ├── post-ner/
│   │   ├── subtitle-gen/
│   │   └── mux/
│   ├── scripts/                 # Stage scripts
│   │   ├── 01_demux.py
│   │   ├── 02_tmdb.py
│   │   ├── 03_pre_ner.py
│   │   ├── 04_silero_vad.py
│   │   ├── 05_pyannote_vad.py
│   │   ├── 06_diarization.py
│   │   ├── 07_asr.py
│   │   ├── 08_post_ner.py
│   │   ├── 09_subtitle_gen.py
│   │   └── 10_mux.py
│   ├── requirements/            # Stage-specific requirements
│   │   ├── demux.txt
│   │   ├── tmdb.txt
│   │   ├── pre_ner.txt
│   │   ├── silero_vad.txt
│   │   ├── pyannote_vad.txt
│   │   ├── diarization.txt
│   │   ├── asr.txt
│   │   ├── post_ner.txt
│   │   ├── subtitle_gen.txt
│   │   └── mux.txt
│   ├── utils/                   # Shared utilities
│   │   ├── device_manager.py    # MPS/CPU detection
│   │   ├── logger.py
│   │   └── manifest.py
│   ├── pipeline.sh              # Main orchestrator
│   ├── setup_venvs.sh           # Create all venvs
│   └── README.md
├── shared/                      # Existing shared code
├── config/                      # Configuration
└── ...
```

---

## Device Manager (MPS/CPU Fallback)

### Strategy
```python
import torch

def get_device(prefer_mps=True):
    """
    Get best available device with automatic fallback.
    
    Priority:
    1. MPS (Mac GPU) if available and preferred
    2. CUDA (if on Linux/Windows with NVIDIA)
    3. CPU (fallback)
    """
    if prefer_mps and torch.backends.mps.is_available():
        try:
            # Test MPS availability
            test_tensor = torch.zeros(1).to('mps')
            return 'mps'
        except Exception as e:
            logger.warning(f"MPS available but failed: {e}, falling back to CPU")
            return 'cpu'
    elif torch.cuda.is_available():
        return 'cuda'
    else:
        return 'cpu'
```

### Per-Stage Device Selection

```python
# Stage 1-2: No ML (demux, tmdb)
device = 'cpu'  # Not applicable

# Stage 3: Pre-NER
device = get_device(prefer_mps=True)  # Benefit from MPS

# Stage 4: Silero VAD
device = get_device(prefer_mps=True)  # High benefit

# Stage 5: PyAnnote VAD
device = get_device(prefer_mps=True)  # High benefit

# Stage 6: Diarization
device = get_device(prefer_mps=True)  # Very high benefit

# Stage 7: ASR (WhisperX)
device = get_device(prefer_mps=True)  # Maximum benefit

# Stage 8: Post-NER
device = get_device(prefer_mps=True)  # Benefit from MPS

# Stage 9-10: No ML (subtitle-gen, mux)
device = 'cpu'  # Not applicable
```

---

## Virtual Environment Setup

### Master Setup Script: `setup_venvs.sh`

```bash
#!/bin/bash
# Creates isolated venvs for each stage

set -e
source scripts/common-logging.sh

VENV_DIR="native/venvs"
REQ_DIR="native/requirements"

log_section "Setting up Native Pipeline Virtual Environments"

# Python version check
PYTHON_CMD="python3.11"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python3"
fi

log_info "Using Python: $($PYTHON_CMD --version)"

# Create venvs for each stage
stages=("demux" "tmdb" "pre-ner" "silero-vad" "pyannote-vad" 
        "diarization" "asr" "post-ner" "subtitle-gen" "mux")

for stage in "${stages[@]}"; do
    log_info "Creating venv for $stage..."
    
    venv_path="$VENV_DIR/$stage"
    req_file="$REQ_DIR/${stage//-/_}.txt"
    
    # Create venv
    $PYTHON_CMD -m venv "$venv_path"
    
    # Install requirements
    if [ -f "$req_file" ]; then
        log_info "  Installing requirements from $req_file"
        "$venv_path/bin/pip" install --quiet --upgrade pip
        "$venv_path/bin/pip" install --quiet -r "$req_file"
        log_success "  $stage venv ready"
    else
        log_warn "  No requirements file found: $req_file"
    fi
done

log_success "All virtual environments created!"
```

---

## Stage Requirements Files

### `native/requirements/asr.txt` (Largest)
```
torch>=2.0.0
torchaudio>=2.0.0
whisperx @ git+https://github.com/m-bain/whisperX.git
transformers>=4.30.0
faster-whisper>=0.9.0
```

### `native/requirements/diarization.txt`
```
torch>=2.0.0
torchaudio>=2.0.0
pyannote-audio>=3.0.0
```

### `native/requirements/pre_ner.txt`
```
torch>=2.0.0
transformers>=4.30.0
spacy>=3.5.0
```

### `native/requirements/silero_vad.txt`
```
torch>=2.0.0
torchaudio>=2.0.0
omegaconf>=2.1.0
```

### `native/requirements/pyannote_vad.txt`
```
torch>=2.0.0
torchaudio>=2.0.0
pyannote-audio>=3.0.0
```

### `native/requirements/tmdb.txt`
```
requests>=2.31.0
```

### `native/requirements/post_ner.txt`
```
torch>=2.0.0
transformers>=4.30.0
rapidfuzz>=3.0.0
```

### `native/requirements/demux.txt`
```
# No Python dependencies, uses system FFmpeg
```

### `native/requirements/subtitle_gen.txt`
```
# Minimal dependencies
```

### `native/requirements/mux.txt`
```
# No Python dependencies, uses system FFmpeg
```

---

## Main Orchestrator: `pipeline.sh`

```bash
#!/bin/bash
# Native MPS-optimized pipeline orchestrator

set -e

# Configuration
INPUT_FILE="$1"
OUTPUT_ROOT="./out"
VENV_DIR="native/venvs"
SCRIPT_DIR="native/scripts"

# Source common logging
source scripts/common-logging.sh

# Validate input
if [ -z "$INPUT_FILE" ]; then
    log_error "Usage: $0 <input_video.mp4>"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    log_error "Input file not found: $INPUT_FILE"
    exit 1
fi

# Extract movie directory name
MOVIE_NAME=$(basename "$INPUT_FILE" .mp4 | sed 's/ /_/g')
MOVIE_DIR="$OUTPUT_ROOT/$MOVIE_NAME"
mkdir -p "$MOVIE_DIR"

log_section "Native MPS Pipeline - Starting"
log_info "Input: $INPUT_FILE"
log_info "Output: $MOVIE_DIR"

# Run stages sequentially
stages=(
    "demux:01_demux.py"
    "tmdb:02_tmdb.py"
    "pre-ner:03_pre_ner.py"
    "silero-vad:04_silero_vad.py"
    "pyannote-vad:05_pyannote_vad.py"
    "diarization:06_diarization.py"
    "asr:07_asr.py"
    "post-ner:08_post_ner.py"
    "subtitle-gen:09_subtitle_gen.py"
    "mux:10_mux.py"
)

for stage_info in "${stages[@]}"; do
    IFS=: read -r stage_name script_name <<< "$stage_info"
    
    log_section "Stage: $stage_name"
    
    venv_path="$VENV_DIR/${stage_name}"
    script_path="$SCRIPT_DIR/$script_name"
    
    if [ ! -d "$venv_path" ]; then
        log_error "Virtual environment not found: $venv_path"
        log_error "Run ./native/setup_venvs.sh first"
        exit 1
    fi
    
    if [ ! -f "$script_path" ]; then
        log_error "Script not found: $script_path"
        exit 1
    fi
    
    # Activate venv and run stage
    log_info "Activating venv: $stage_name"
    
    (
        source "$venv_path/bin/activate"
        log_info "Running: $script_name"
        
        python "$script_path" \
            --input "$INPUT_FILE" \
            --movie-dir "$MOVIE_DIR" \
            --config "config/.env"
        
        if [ $? -eq 0 ]; then
            log_success "$stage_name completed"
        else
            log_failure "$stage_name failed"
            exit 1
        fi
    )
    
    if [ $? -ne 0 ]; then
        log_error "Pipeline failed at stage: $stage_name"
        exit 1
    fi
done

log_section "Pipeline Complete!"
log_success "Output: $MOVIE_DIR"
```

---

## Device Manager Implementation

### `native/utils/device_manager.py`

```python
"""
Device manager for MPS/CPU fallback logic
"""
import torch
import logging
from typing import Literal

logger = logging.getLogger(__name__)

DeviceType = Literal['mps', 'cuda', 'cpu']


class DeviceManager:
    """Manages device selection with automatic fallback."""
    
    def __init__(self):
        self._mps_available = torch.backends.mps.is_available()
        self._cuda_available = torch.cuda.is_available()
        self._mps_tested = False
        self._mps_working = False
    
    def get_device(self, prefer_mps: bool = True) -> DeviceType:
        """
        Get best available device.
        
        Args:
            prefer_mps: Prefer MPS over CPU if available
        
        Returns:
            Device string: 'mps', 'cuda', or 'cpu'
        """
        # CUDA takes priority (if on Linux/Windows)
        if self._cuda_available:
            logger.info("Using CUDA device")
            return 'cuda'
        
        # Try MPS if preferred and available
        if prefer_mps and self._mps_available:
            if not self._mps_tested:
                self._test_mps()
            
            if self._mps_working:
                logger.info("Using MPS device (Mac GPU)")
                return 'mps'
        
        # Fallback to CPU
        logger.info("Using CPU device")
        return 'cpu'
    
    def _test_mps(self):
        """Test if MPS actually works."""
        try:
            test_tensor = torch.zeros(1, device='mps')
            test_result = test_tensor + 1
            self._mps_working = True
            self._mps_tested = True
            logger.info("MPS test passed")
        except Exception as e:
            self._mps_working = False
            self._mps_tested = True
            logger.warning(f"MPS test failed: {e}")
    
    @property
    def has_mps(self) -> bool:
        """Check if MPS is available and working."""
        if not self._mps_tested:
            self._test_mps()
        return self._mps_working
    
    @property
    def has_cuda(self) -> bool:
        """Check if CUDA is available."""
        return self._cuda_available


# Global instance
device_manager = DeviceManager()


def get_device(prefer_mps: bool = True) -> str:
    """Convenience function to get device."""
    return device_manager.get_device(prefer_mps)
```

---

## Example Stage Script Template

### `native/scripts/07_asr.py` (ASR with MPS)

```python
#!/usr/bin/env python3
"""
Stage 7: ASR (Automatic Speech Recognition)
Uses WhisperX with MPS acceleration
"""
import sys
import argparse
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

from device_manager import get_device
from logger import setup_logger
from manifest import StageManifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--movie-dir', required=True)
    parser.add_argument('--config', default='config/.env')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    logger = setup_logger('asr')
    
    # Get best device (MPS preferred for ASR)
    device = get_device(prefer_mps=True)
    logger.info(f"Using device: {device}")
    
    with StageManifest('asr', movie_dir, logger) as manifest:
        # Import WhisperX (inside venv)
        import whisperx
        
        # Load audio
        audio_file = movie_dir / 'audio' / 'audio.wav'
        logger.info(f"Loading audio: {audio_file}")
        
        audio = whisperx.load_audio(str(audio_file))
        
        # Load model with device
        logger.info(f"Loading WhisperX model on {device}")
        model = whisperx.load_model(
            "large-v3",
            device=device,
            compute_type="float16" if device != 'cpu' else "int8"
        )
        
        # Transcribe
        logger.info("Transcribing...")
        result = model.transcribe(
            audio,
            language="hi",
            task="translate"  # Hindi -> English
        )
        
        # Save output
        output_file = movie_dir / 'transcription' / 'transcript.json'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Record in manifest
        manifest.add_output('transcript', output_file, 'WhisperX transcript')
        manifest.add_metadata('model', 'large-v3')
        manifest.add_metadata('device', device)
        manifest.add_metadata('language', 'hi')
        manifest.add_metadata('task', 'translate')
        
        logger.info(f"✓ ASR completed on {device}")


if __name__ == '__main__':
    main()
```

---

## Benefits vs Docker

| Aspect | Docker | Native MPS |
|--------|--------|------------|
| **Speed** | Slower (overhead) | Faster (native) |
| **GPU** | Limited MPS support | Full MPS acceleration |
| **Setup** | Build images | Create venvs |
| **Resources** | Higher memory | Lower memory |
| **Debugging** | Harder | Easier |
| **Isolation** | Container-level | venv-level |
| **Portability** | High | Medium |

---

## Setup Instructions

```bash
# 1. Create directory structure
mkdir -p native/{venvs,scripts,requirements,utils}

# 2. Create requirements files
# (see above)

# 3. Create setup script
./native/setup_venvs.sh

# 4. Run pipeline
./native/pipeline.sh "in/movie.mp4"
```

---

## Expected Performance Improvements

| Stage | Docker (CPU) | Native (MPS) | Speedup |
|-------|--------------|--------------|---------|
| demux | 43s | 43s | 1x (FFmpeg) |
| tmdb | 2s | 2s | 1x (API) |
| pre-ner | 2s | 1s | 2x |
| silero-vad | 16m | 3-5m | 3-5x |
| pyannote-vad | 57m | 10-15m | 4-6x |
| diarization | 15-30m | 5-10m | 3x |
| asr | 30-60m | 10-20m | 3x |
| post-ner | 2-5m | 1-2m | 2x |
| subtitle-gen | 1-2m | 1-2m | 1x |
| mux | 2-5m | 2-5m | 1x |
| **Total** | **2-3.5h** | **0.5-1h** | **3-4x** |

---

## Next Steps

1. Create directory structure
2. Write all requirements files
3. Implement device_manager.py
4. Create setup_venvs.sh
5. Write stage scripts (01-10)
6. Create pipeline.sh orchestrator
7. Test each stage individually
8. Run full pipeline

---

**Status**: Design complete, ready for implementation!
