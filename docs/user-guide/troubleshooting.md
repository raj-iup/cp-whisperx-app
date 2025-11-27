# Troubleshooting Guide

Comprehensive guide to resolving common issues with cp-whisperx-app multi-environment pipeline.

---

## Table of Contents

- [Environment Issues](#environment-issues)
- [PyAnnote and Demucs Environments](#pyannote-and-demucs-environments)
- [Deprecated Install Scripts](#deprecated-install-scripts)
- [MLX Issues (Apple Silicon)](#mlx-issues-apple-silicon)
- [IndicTrans2 Issues](#indictrans2-issues)
- [Dependency Conflicts](#dependency-conflicts)
- [Pipeline Failures](#pipeline-failures)
- [Performance Issues](#performance-issues)
- [Windows-Specific Issues](#windows-specific-issues)
- [Diagnostic Commands](#diagnostic-commands)

---

## Environment Issues

### Error: "Environment not found" or "Bootstrap not run"

**Symptom**:
```bash
[ERROR] venv/mlx virtual environment not found
[INFO] Please run ./bootstrap.sh first
```
OR
```bash
[ERROR] Hardware cache not found
[INFO] Please run: ./bootstrap.sh
```

**Cause**: Multi-environment setup hasn't been completed by bootstrap

**Solution**:
```bash
# Create all 4 environments (common, whisperx, mlx, indictrans2)
./bootstrap.sh

# This creates:
#   venv/common      - Lightweight utilities (subtitle generation, muxing)
#   venv/whisperx    - WhisperX ASR engine (CUDA/CPU)
#   venv/mlx         - MLX-Whisper for Apple Silicon (M1/M2/M3) - 6-8x faster
#   venv/indictrans2 - IndicTrans2 translation for 22 Indic languages
# Plus config/hardware_cache.json for environment mappings

# Verify all environments were created
ls -la .venv-*

# Check hardware cache
cat config/hardware_cache.json | jq .hardware

# On Windows PowerShell:
.\bootstrap.ps1
```

**Why Multiple Environments?**
- Different ML frameworks have conflicting dependencies
- WhisperX requires torch 2.0.x, numpy <2.0
- IndicTrans2 requires torch 2.5+, numpy 2.1+
- Pipeline automatically switches environments per stage

---

### Error: "Missing environments: common, whisperx"

**Symptom**:
```bash
[ERROR] Missing environments: common, whisperx
[INFO] Please run: ./bootstrap.sh
```

**Cause**: Some environments failed to install during bootstrap

**Solution**:
```bash
# Check which environments exist
ls -la .venv-*

# Re-create missing environments
./bootstrap.sh --env common
./bootstrap.sh --env whisperx

# Or rebuild all
./bootstrap.sh --clean
./bootstrap.sh
```

---

### Error: "jq is required but not installed"

**Symptom**:
```bash
[ERROR] jq is required but not installed
[INFO] Install with: brew install jq
```

**Cause**: `jq` JSON processor not installed (required for hardware cache parsing)

**Solution**:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq

# CentOS/RHEL
sudo yum install jq

# Verify installation
jq --version
```

---

## PyAnnote and Demucs Environments

### Error: "Unknown environment: pyannote" or "Unknown environment: demucs"

**Symptom**:
```bash
[ERROR] Unexpected error in PyAnnote VAD: Unknown environment: pyannote
[ERROR] Pipeline cannot continue without VAD preprocessing
[ERROR] PIPELINE FAILED
```
OR
```bash
[ERROR] Unknown environment: demucs
[ERROR] Source separation failed
```

**Cause**: PyAnnote VAD and/or Demucs source separation environments were not installed during bootstrap, or bootstrap was run from an older version.

**Why These Are Required**:
- **PyAnnote VAD**: Voice Activity Detection - Critical for accurate speech segment detection
- **Demucs**: Audio source separation - Essential for isolating dialogue from background music
- Both ensure highest quality transcription output, especially for Indian movies/content

**Solution: Re-run Bootstrap**

Bootstrap now installs ALL environments including PyAnnote and Demucs:

```bash
# Re-run bootstrap (will skip already-installed environments)
./bootstrap.sh

# Verify all 7 environments exist
ls -la .venv-*

# Should show:
# venv/common
# venv/whisperx
# venv/mlx (if Apple Silicon)
# venv/pyannote  ← Required for VAD
# venv/demucs    ← Required for source separation
# venv/indictrans2
# venv/nllb
```

**Force Recreate All Environments** (if needed):
```bash
./bootstrap.sh --force
```

**Verify Installation**:
```bash
# Check hardware cache includes all environments
cat config/hardware_cache.json | jq '.environments | keys'
# Should include: "common", "demucs", "indictrans2", "mlx", "nllb", "pyannote", "whisperx"

# Test PyAnnote
source venv/pyannote/bin/activate
python -c "import pyannote.audio; print('✓ PyAnnote working')"
deactivate

# Test Demucs
source venv/demucs/bin/activate  
python -c "import demucs; print('✓ Demucs working')"
deactivate
```

**When These Features Are Used**:
- **PyAnnote VAD**: Used in all transcription workflows for speech detection
- **Demucs**: Used when source_separation is enabled in job config
- **Both required**: For production-quality output, especially with movies/music

---

### Error: "No module named 'torchcodec'" (Demucs)

**Symptom**:
```bash
[INFO] Processing audio with Demucs...
[100%] ████████████████████████████████████ 602.55/602.55
ModuleNotFoundError: No module named 'torchcodec'
ImportError: TorchCodec is required for save_with_torchcodec
[ERROR] Source separation failed
```

**Cause**: Demucs environment has incompatible torch/torchaudio versions (2.9.x) that require torchcodec.

**Solution: Recreate Demucs Environment**

```bash
# Remove old demucs environment
rm -rf venv/demucs

# Re-run bootstrap (uses fixed requirements with torch 2.5.1)
./bootstrap.sh

# Verify correct versions
source venv/demucs/bin/activate
python -c "import torch; print(f'torch: {torch.__version__}')"
python -c "import torchaudio; print(f'torchaudio: {torchaudio.__version__}')"
deactivate

# Expected: torch: 2.5.1, torchaudio: 2.5.1
```

**Why This Happens**:
- torchaudio 2.9.x tries to use torchcodec for audio encoding
- torchcodec not available via standard pip install
- Demucs works fine with torchaudio 2.5.1 (no torchcodec needed)

**Technical Details**: See `docs/technical/DEMUCS_TORCHCODEC_FIX.md`

---

## Deprecated Install Scripts

### Using install-mlx.sh or install-indictrans2.sh

**Important**: These scripts are **DEPRECATED** but kept for backward compatibility.

**Old Way (Deprecated)**:
```bash
./install-mlx.sh          # ❌ Old method
./install-indictrans2.sh  # ❌ Old method
```

**New Way (Current)**:
```bash
./bootstrap.sh            # ✅ Creates ALL environments automatically
```

**What Changed**:
- **Old**: Single `.bollyenv` environment with manual component installation
- **New**: Multi-environment architecture (`venv/common`, `venv/whisperx`, `venv/mlx`, `venv/indictrans2`)
- **Why**: Prevents dependency conflicts between WhisperX (numpy <2.0) and IndicTrans2 (numpy >=2.1)

**If You Run Deprecated Scripts**:
```bash
# They now simply forward to bootstrap.sh
./install-mlx.sh          # → Runs ./bootstrap.sh
./install-indictrans2.sh  # → Runs ./bootstrap.sh
```

**Migration from Old Setup**:
```bash
# Remove old single environment
rm -rf .bollyenv

# Create new multi-environment setup
./bootstrap.sh

# Verify all 4 environments exist
ls -la .venv-*
# Should show: venv/common, venv/whisperx, venv/mlx, venv/indictrans2
```

**Key Benefits of New Architecture**:
- ✅ No dependency conflicts
- ✅ Automatic per-stage environment switching
- ✅ Transparent to user (workflows unchanged)
- ✅ Easy to maintain/update each environment separately
- ✅ 6-8x faster transcription with MLX on Apple Silicon
- ✅ 90% faster translation with IndicTrans2 for Indic languages

---

## MLX Issues (Apple Silicon)

### MLX Not Working on Apple Silicon

**Symptom**:
```bash
[WARN] MLX not available, falling back to WhisperX
[INFO] Running ASR with WhisperX backend
```

**Diagnosis Steps**:

1. **Check if running on Apple Silicon**:
```bash
uname -m
# Should output: arm64
```

2. **Check if MLX environment exists**:
```bash
ls -la venv/mlx
# Should exist
```

3. **Check if MLX is installed**:
```bash
source venv/mlx/bin/activate
python -c "import mlx.core as mx; print(mx.array([1,2,3]))"
deactivate
```

**Solutions**:

**Solution 1: Re-create MLX environment**
```bash
# Remove existing environment
rm -rf venv/mlx

# Recreate
./bootstrap.sh --env mlx

# Verify
source venv/mlx/bin/activate
python -c "import mlx.core as mx; import mlx_whisper; print('✓ MLX working')"
deactivate
```

**Solution 2: Full re-bootstrap**
```bash
./bootstrap.sh --clean
./bootstrap.sh
```

---

### MLX Import Error: "No module named 'mlx'"

**Symptom**:
```python
ModuleNotFoundError: No module named 'mlx'
```

**Cause**: MLX not installed in `venv/mlx` environment

**Solution**:
```bash
# Activate MLX environment
source venv/mlx/bin/activate

# Install MLX manually
pip install mlx>=0.4.0
pip install mlx-whisper>=0.3.0

# Verify
python -c "import mlx.core as mx; print('MLX:', mx.__version__)"
python -c "import mlx_whisper; print('MLX-Whisper installed')"

deactivate

# Update hardware cache
./bootstrap.sh
```

---

### MLX Performance Slower Than Expected

**Symptom**: ASR taking longer than expected on Apple Silicon

**Diagnosis**:
```bash
# Check if MPS is being used
cat config/.env.pipeline | grep DEVICE

# Should show: DEVICE=mps
```

**Solutions**:

1. **Verify MPS is detected**:
```bash
source venv/mlx/bin/activate
python -c "
import torch
print('MPS available:', torch.backends.mps.is_available())
print('MPS built:', torch.backends.mps.is_built())
"
deactivate
```

2. **Check batch size**:
```bash
# Edit config/.env.pipeline
BATCH_SIZE_ASR=8  # Try lower value for M1
BATCH_SIZE_ASR=16 # Try higher for M3
```

3. **Monitor memory usage**:
```bash
# Run pipeline with Activity Monitor open
# Check memory pressure in GPU History tab
```

---

## IndicTrans2 Issues

### IndicTrans2 Authentication Error

**Symptom**:
```bash
[ERROR] 401 Unauthorized - gated model access required
[ERROR] Could not download IndicTrans2 model
```

**Cause**: HuggingFace model access not granted or not authenticated

**Solution**:

**Step 1: Request Model Access**
```bash
# Visit model page
open https://huggingface.co/ai4bharat/indictrans2-indic-en-1B

# Click "Agree and access repository"
# Wait for approval (usually instant)
```

**Step 2: Authenticate**
```bash
# Activate IndicTrans2 environment
source venv/indictrans2/bin/activate

# Login to HuggingFace
huggingface-cli login
# Paste your HuggingFace token when prompted

# Verify authentication
python -c "
from huggingface_hub import HfFolder
token = HfFolder.get_token()
print('✓ Authenticated' if token else '✗ Not authenticated')
"

deactivate
```

**Step 3: Re-run Bootstrap**
```bash
# Download model with authentication
./bootstrap.sh --env indictrans2
```

---

### IndicTrans2 Model Download Fails

**Symptom**:
```bash
[ERROR] Failed to download model: ai4bharat/indictrans2-indic-en-1B
```

**Diagnosis**:
```bash
# Check disk space
df -h .cache/huggingface

# Should have ~5GB free for model download
```

**Solutions**:

**Solution 1: Clear cache and retry**
```bash
# Clear HuggingFace cache
rm -rf .cache/huggingface/*

# Re-download
source venv/indictrans2/bin/activate
huggingface-cli login
python -c "
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model_name = 'ai4bharat/indictrans2-indic-en-1B'
print('Downloading tokenizer...')
tokenizer = AutoTokenizer.from_pretrained(model_name)
print('Downloading model... (this may take a while)')
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print('✓ Model downloaded successfully')
"
deactivate
```

**Solution 2: Manual download with resume**
```bash
source venv/indictrans2/bin/activate

python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    'ai4bharat/indictrans2-indic-en-1B',
    resume_download=True,
    local_dir_use_symlinks=False
)
"

deactivate
```

---

### IndicTrans2 Translation Quality Issues

**Symptom**: Poor translation quality or unexpected output

**Diagnosis Steps**:

1. **Check beam search settings**:
```bash
cat config/.env.pipeline | grep INDICTRANS2

# Should see:
# INDICTRANS2_NUM_BEAMS=4  # Higher = better quality, slower
```

2. **Verify language code**:
```bash
# Ensure source language is correct Indic code
# hi (Hindi), ta (Tamil), te (Telugu), etc.
```

**Solutions**:

**Solution 1: Increase translation quality**
```bash
# Edit config/.env.pipeline
INDICTRANS2_NUM_BEAMS=8           # Higher quality (slower)
INDICTRANS2_MAX_NEW_TOKENS=256    # Longer translations
```

**Solution 2: Check IndicTransToolkit**
```bash
source venv/indictrans2/bin/activate

# Check if toolkit is installed
python -c "
try:
    import IndicTransToolkit
    print('✓ IndicTransToolkit installed')
except ImportError:
    print('✗ IndicTransToolkit not installed')
    print('Installing...')
"

# Install if missing
pip install IndicTransToolkit

deactivate
```

---

## Dependency Conflicts

### Error: "Cannot install torch 2.0.0 and torch 2.5.0"

**Symptom**:
```bash
ERROR: Cannot install torch==2.0.0 and torch>=2.5.0 at the same time
```

**Cause**: Manually activating wrong environment or mixing packages

**Explanation**: This is WHY we have multi-environment architecture:
- `venv/whisperx` needs `torch==2.0.x`
- `venv/indictrans2` needs `torch>=2.5.0`

**Solution**:

**❌ DON'T manually activate environments**:
```bash
# This will cause conflicts!
source venv/whisperx/bin/activate
pip install transformers  # Wrong environment!
```

**✅ DO let scripts handle environments**:
```bash
# Scripts automatically select correct environment per stage
./run-pipeline.sh -j <job-id>
```

**If already broken**:
```bash
# Rebuild affected environments
./bootstrap.sh --clean
./bootstrap.sh
```

---

### NumPy Version Conflicts

**Symptom**:
```bash
ERROR: whisperx requires numpy<2.0 but numpy 2.1.0 is installed
```

**Cause**: Wrong environment or manual pip install in wrong environment

**Solution**:
```bash
# Check which environment has wrong numpy
source venv/whisperx/bin/activate
python -c "import numpy; print(numpy.__version__)"
deactivate
# Should be: 1.23.x - 1.26.x

source venv/indictrans2/bin/activate
python -c "import numpy; print(numpy.__version__)"
deactivate
# Should be: 2.1.x+

# Fix wrong environment
rm -rf venv/whisperx  # or venv/indictrans2
./bootstrap.sh --env whisperx  # or indictrans2
```

---

## Pipeline Failures

### Pipeline Stops at ASR Stage

**Symptom**:
```bash
[INFO] Running stage: asr
[ERROR] ASR stage failed
```

**Diagnosis**:
```bash
# Check ASR log
cat out/YYYY/MM/DD/[UserID]/[counter]/logs/asr.log | tail -50

# Common errors:
# - "CUDA out of memory" → Reduce batch size
# - "MPS backend not available" → Wrong device setting
# - "Model not found" → Model not downloaded
```

**Solutions**:

**Solution 1: Reduce batch size**
```bash
# Edit config/.env.pipeline
BATCH_SIZE_ASR=4  # Lower for limited memory
```

**Solution 2: Change device**
```bash
# Edit config/.env.pipeline
DEVICE=cpu  # Force CPU if GPU issues
```

**Solution 3: Re-download models**
```bash
# Clear model cache
rm -rf .cache/torch/*
rm -rf .cache/huggingface/*

# Re-run bootstrap
./bootstrap.sh
```

---

### Pipeline Stops at Translation Stage

**Symptom**:
```bash
[INFO] Running stage: indictrans2_translation
[ERROR] Translation stage failed
```

**Diagnosis**:
```bash
# Check translation log
cat out/YYYY/MM/DD/[UserID]/[counter]/logs/translation.log

# Check if transcript exists
cat out/YYYY/MM/DD/[UserID]/[counter]/transcripts/segments.json | jq .
```

**Solutions**:

**Solution 1: Verify transcript**
```bash
# Check if segments exist
jq '.segments | length' out/.../transcripts/segments.json

# Should have segments with text
jq '.segments[0]' out/.../transcripts/segments.json
```

**Solution 2: Check IndicTrans2 environment**
```bash
source venv/indictrans2/bin/activate

# Verify transformers version
pip show transformers | grep Version
# Should be: 4.51.0 or higher

# Verify model can be loaded
python -c "
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model_name = 'ai4bharat/indictrans2-indic-en-1B'
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print('✓ Model can be loaded')
except Exception as e:
    print(f'✗ Error: {e}')
"

deactivate
```

---

### Subtitle Generation Fails

**Symptom**:
```bash
[INFO] Running stage: subtitle_generation
[ERROR] Failed to generate subtitles
```

**Diagnosis**:
```bash
# Check subtitle log
cat out/YYYY/MM/DD/[UserID]/[counter]/logs/subtitle_gen.log

# Check if translated segments exist
ls -la out/YYYY/MM/DD/[UserID]/[counter]/transcripts/
```

**Solution**:
```bash
# Verify common environment
source venv/common/bin/activate

# Check if srt package is installed
python -c "
try:
    import srt
    print('✓ srt package installed')
except ImportError:
    print('✗ srt package missing')
"

deactivate

# Re-create common environment if needed
./bootstrap.sh --env common
```

---

## Performance Issues

### Transcription Too Slow

**Expected Performance**:
- **MLX (Apple Silicon)**: 1 hour audio = 5-10 minutes
- **WhisperX (CUDA)**: 1 hour audio = 15-25 minutes
- **WhisperX (CPU)**: 1 hour audio = 60-120 minutes

**If slower than expected**:

1. **Check which backend is being used**:
```bash
# Look for this in logs
grep "Using.*backend" out/.../logs/asr.log

# Should see:
# "Using MLX backend" (Apple Silicon)
# or "Using WhisperX backend with CUDA"
```

2. **Check batch size**:
```bash
cat config/.env.pipeline | grep BATCH_SIZE

# Increase if using GPU:
BATCH_SIZE_ASR=16  # For good GPU
BATCH_SIZE_ASR=8   # For limited memory
```

3. **Check model size**:
```bash
cat config/.env.pipeline | grep WHISPER_MODEL

# Try smaller model for speed:
WHISPER_MODEL=medium  # Faster, less accurate
WHISPER_MODEL=large-v3  # Slower, more accurate
```

---

### Translation Too Slow

**Expected Performance**:
- 1 hour of segments = 2-5 minutes translation

**If slower**:

1. **Check beam search setting**:
```bash
cat config/.env.pipeline | grep INDICTRANS2_NUM_BEAMS

# Reduce for speed:
INDICTRANS2_NUM_BEAMS=1  # Fastest, lower quality
INDICTRANS2_NUM_BEAMS=4  # Balanced (default)
INDICTRANS2_NUM_BEAMS=8  # Best quality, slower
```

2. **Check batch size**:
```bash
cat config/.env.pipeline | grep BATCH_SIZE_TRANSLATION

# Increase for speed:
BATCH_SIZE_TRANSLATION=32  # If GPU has memory
```

---

## Windows-Specific Issues

### Developer Mode Not Enabled

**Symptom**:
```powershell
[WARN] Windows Developer Mode not enabled
[INFO] HuggingFace cache will use more disk space without symlinks
```

**Impact**: 5-10 GB extra disk usage

**Solution**:
```powershell
# Enable Developer Mode
# Settings → Privacy & security → For developers → Developer Mode ON

# Restart PowerShell after enabling
# Re-run bootstrap
.\bootstrap.ps1
```

---

### PowerShell Execution Policy Error

**Symptom**:
```powershell
.\bootstrap.ps1 : File cannot be loaded because running scripts is disabled
```

**Solution**:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run bootstrap
.\bootstrap.ps1
```

---

### CUDA Not Detected on Windows

**Symptom**:
```powershell
[INFO] CUDA not detected, using CPU
```

**Diagnosis**:
```powershell
# Check if NVIDIA GPU exists
nvidia-smi

# Check CUDA version
nvcc --version
```

**Solutions**:

1. **Install CUDA Toolkit**:
```powershell
# Download and install CUDA 11.8 or 12.1
# From: https://developer.nvidia.com/cuda-downloads
```

2. **Install PyTorch with CUDA**:
```powershell
# Activate whisperx environment
.\venv/whisperx\Scripts\Activate.ps1

# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

deactivate

# Re-run bootstrap
.\bootstrap.ps1
```

---

## Cache Issues

### Models Downloading Multiple Times

**Symptom**: 
- Models re-download every pipeline run
- Large disk usage from duplicate models
- Slow pipeline startup

**Cause**: Cache environment variables not properly set or cache directory issues

**Diagnosis**:
```bash
# Check cache status
./scripts/cache-manager.sh status

# Check cache environment variables
cat config/hardware_cache.json | jq .cache

# Look for models in multiple locations
du -sh ~/.cache/torch ~/.cache/huggingface .cache/torch .cache/huggingface 2>/dev/null
```

**Solution**:
```bash
# Re-run bootstrap to regenerate cache configuration
./bootstrap.sh --force

# Verify cache paths are set
cat config/hardware_cache.json | jq .cache

# Expected output:
# {
#   "base_dir": ".cache",
#   "torch_home": ".cache/torch",
#   "hf_home": ".cache/huggingface",
#   ...
# }

# Clean up duplicate caches (optional)
# WARNING: This will re-download models
rm -rf ~/.cache/torch ~/.cache/huggingface
```

---

### Disk Space Issues

**Symptom**: Running out of disk space during bootstrap or pipeline execution

**Diagnosis**:
```bash
# Check total cache size
./scripts/cache-manager.sh status

# Check specific cache sizes
du -sh .cache/*
du -sh out/*_cache

# Check available disk space
df -h .
```

**Solutions**:

**Option 1: Clear old model versions**
```bash
# Clear model caches (will re-download on next use)
./scripts/cache-manager.sh clear-models

# Or manually:
rm -rf .cache/torch/hub/
rm -rf .cache/huggingface/hub/
```

**Option 2: Use smaller Whisper model**
```bash
# Edit job configuration before running pipeline
# Change "large-v3" to "base" or "medium"
# base: ~150MB, medium: ~1.5GB, large-v3: ~3GB
```

**Option 3: Mount cache on external drive**
```bash
# Move cache to external drive
mv .cache /Volumes/External/cp-whisperx-cache

# Create symlink
ln -s /Volumes/External/cp-whisperx-cache .cache

# Verify
ls -la .cache
```

**Option 4: Clear application caches**
```bash
# Clear TMDB, MusicBrainz, glossary caches
./scripts/cache-manager.sh clear-app

# These will auto-refresh as needed (90-day expiry)
```

---

### Legacy Cache Directory Warning

**Symptom**:
```bash
⚠️  Legacy Model Cache (should be empty)
   Location: shared/model-cache/
   Size:     17M
   Files:    82
```

**Cause**: Old cache structure from previous versions

**Solution**:
```bash
# Safe to delete - models now in .cache/
rm -rf shared/model-cache/

# Verify new cache is used
./scripts/cache-manager.sh status
# Should show models only in .cache/
```

---

### Cache Permission Issues

**Symptom**:
- "Permission denied" when downloading models
- "Cannot write to cache directory" errors

**Diagnosis**:
```bash
# Check cache directory permissions
ls -la .cache/
ls -la .cache/torch/
ls -la .cache/huggingface/
```

**Solution**:
```bash
# Fix permissions
chmod -R u+w .cache/

# Or recreate cache directories
rm -rf .cache/
./bootstrap.sh --force
```

---

## Diagnostic Commands

### Check System Health

```bash
# 1. Check all environments exist
./bootstrap.sh --check

# 2. Verify hardware detection
cat config/hardware_cache.json | jq .hardware

# 3. Check Python versions
for env in common whisperx indictrans2 mlx; do
  echo "=== $env ==="
  ./.venv-$env/bin/python --version
done

# 4. Check key packages
source venv/mlx/bin/activate && pip list | grep -E "(mlx|numpy)" && deactivate
source venv/whisperx/bin/activate && pip list | grep -E "(whisperx|torch|numpy)" && deactivate
source venv/indictrans2/bin/activate && pip list | grep -E "(transformers|torch|numpy)" && deactivate

# 5. Check logs
ls -lth logs/ | head -10
```

### Check Job Status

```bash
# Find job directory
find out -type d -name "<job-id>"

# Check manifest
cat out/.../job.json | jq .

# Check stage logs
ls -la out/.../logs/

# Check which environment was used
grep "Using environment" out/.../logs/pipeline.log
```

### Debug Mode

```bash
# Enable maximum verbosity
export LOG_LEVEL=DEBUG

# Run with debug flag
./prepare-job.sh movie.mp4 --transcribe -s hi --debug
./run-pipeline.sh -j <job-id> --debug

# Check debug log
cat logs/*-debug.log
```

### Environment Verification Script

```bash
#!/bin/bash
# Save as: check_health.sh

echo "=== CP-WhisperX-App Health Check ==="
echo ""

echo "1. Checking environments..."
./bootstrap.sh --check

echo ""
echo "2. Checking hardware cache..."
if [ -f config/hardware_cache.json ]; then
  echo "✓ Hardware cache exists"
  jq .hardware config/hardware_cache.json
else
  echo "✗ Hardware cache missing"
fi

echo ""
echo "3. Checking MLX (Apple Silicon)..."
if [ -d venv/mlx ]; then
  source venv/mlx/bin/activate
  python -c "import mlx.core as mx; print('✓ MLX working')" 2>&1 || echo "✗ MLX not working"
  deactivate
fi

echo ""
echo "4. Checking IndicTrans2..."
if [ -d venv/indictrans2 ]; then
  source venv/indictrans2/bin/activate
  python -c "from transformers import AutoTokenizer; print('✓ Transformers working')" 2>&1 || echo "✗ Transformers not working"
  deactivate
fi

echo ""
echo "5. Recent logs..."
ls -lt logs/ | head -5

echo ""
echo "=== Health Check Complete ==="
```

---

## Getting More Help

1. **Enable debug logging**: `export LOG_LEVEL=DEBUG` or add `--debug` flag
2. **Check logs**: Always review logs in `logs/` and job directories
3. **Verify environments**: Run `./bootstrap.sh --check`
4. **Clean and rebuild**: `./bootstrap.sh --clean && ./bootstrap.sh`
5. **Check documentation**: Review README.md and QUICK_REFERENCE.md

**Still stuck?** Check the specific log file mentioned in the error message.
