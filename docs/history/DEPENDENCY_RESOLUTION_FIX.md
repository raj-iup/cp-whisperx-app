# Dependency Resolution Fix for cp-whisperx-app

## Problem
When installing dependencies with `requirements.txt` or `requirements-macos.txt`, pip was encountering "resolution-too-deep" errors due to complex dependency conflicts between:
- PyTorch/torchaudio versions
- WhisperX and its dependencies
- PyAnnote.audio versions
- HuggingFace transformers and tokenizers

## Solution
Created `requirements-macos-pinned.txt` with fully pinned versions that are known to work together on macOS Apple Silicon (M1/M2/M3).

## Usage

### For New Installations
```bash
pip install -r requirements-macos-pinned.txt
```

### For Existing Environments
If you already have a working environment, you can continue using it. The pinned file is based on tested working versions:
- torch==2.8.0 (with MPS support)
- whisperx==3.4.3
- pyannote.audio==3.4.0
- transformers==4.57.0

## Key Version Constraints

The following version constraints are critical for compatibility:

1. **PyTorch**: 2.8.0 (provides best MPS support for Apple Silicon)
2. **NumPy**: 1.26.4 (newer 2.x versions cause conflicts)
3. **PyAnnote**: 3.4.0 (must match whisperx requirements)
4. **WhisperX**: 3.4.3 (latest stable)
5. **av**: 15.1.0 (compatible with modern ffmpeg)
6. **faster-whisper**: 1.2.0
7. **ctranslate2**: 4.4.0

## Why This Works

1. **Pinned versions** eliminate pip's need to backtrack through version combinations
2. **Tested combination** - these versions are from a working environment
3. **Apple Silicon optimized** - PyTorch 2.8.0 has excellent MPS (Metal Performance Shaders) support
4. **Modern dependencies** - Uses current stable versions of all major packages

## Troubleshooting

If you still encounter issues:

1. **Upgrade pip first**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Clear pip cache**:
   ```bash
   pip cache purge
   ```

3. **Use a fresh virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or `.venv/bin/activate.fish` for fish shell
   pip install --upgrade pip
   pip install -r requirements-macos-pinned.txt
   ```

## Alternative: Flexible Requirements

If you need more flexibility, use `requirements-flexible.txt` which has version ranges instead of pinned versions, but be prepared for longer resolution times.

## Date
Created: 2025-11-08
Python Version: 3.11.13
Platform: macOS (Apple Silicon)
