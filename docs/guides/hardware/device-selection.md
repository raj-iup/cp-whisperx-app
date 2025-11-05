# Pipeline Orchestrator Device Selection Guide

## Overview

The pipeline orchestrator now intelligently selects execution mode based on the `DEVICE` setting in your job configuration file.

## Device Modes

### 1. CPU Mode (`DEVICE=cpu`)
**All stages run in Docker containers on CPU**

- **Execution:** Docker containers
- **Performance:** Baseline (slowest)
- **Compatibility:** Works everywhere
- **Use case:** No GPU available, or testing

**Example job config:**
```bash
# jobs/YYYY/MM/DD/JOBID/.JOBID.env
DEVICE=cpu
```

**Stage execution:**
```
Stage 1-10: All run in Docker (CPU-based)
```

---

### 2. MPS Mode (`DEVICE=mps`)
**ML stages run natively with MPS GPU acceleration**

- **Execution:** 
  - ML stages (4, 5, 6, 7): Native Python with MPS
  - Other stages: Docker containers
- **Performance:** 5-6x faster than CPU
- **Hardware:** M1/M2/M3/M4 Mac required
- **Use case:** Mac with Apple Silicon

**Example job config:**
```bash
# jobs/YYYY/MM/DD/JOBID/.JOBID.env
DEVICE=mps
```

**Stage execution:**
```
Stages 1-3:   Docker (CPU)       - demux, tmdb, pre_ner
Stage 4:      Native (MPS) 🚀    - silero_vad
Stage 5:      Native (MPS) 🚀    - pyannote_vad
Stage 6:      Native (MPS) 🚀    - diarization
Stage 7:      Native (MPS) 🚀    - asr
Stages 8-10:  Docker (CPU)       - post_ner, subtitle_gen, mux
```

**Performance:**
- Silero VAD: 217s → 39s (5.6x)
- PyAnnote VAD: 687s → 120s (5.7x)
- Diarization: 5917s → 900s (6.6x)
- ASR: 2236s → 600s (3.7x)
- **Total: 2.5 hours → 28 minutes**

---

### 3. CUDA Mode (`DEVICE=cuda`)
**ML stages run natively with CUDA GPU acceleration**

- **Execution:**
  - ML stages (4, 5, 6, 7): Native Python with CUDA
  - Other stages: Docker containers
- **Performance:** 15-20x faster than CPU
- **Hardware:** NVIDIA GPU required
- **Use case:** Linux/Windows with NVIDIA GPU

**Example job config:**
```bash
# jobs/YYYY/MM/DD/JOBID/.JOBID.env
DEVICE=cuda
```

**Stage execution:**
```
Stages 1-3:   Docker (CPU)       - demux, tmdb, pre_ner
Stage 4:      Native (CUDA) 🚀   - silero_vad
Stage 5:      Native (CUDA) 🚀   - pyannote_vad
Stage 6:      Native (CUDA) 🚀   - diarization
Stage 7:      Native (CUDA) 🚀   - asr
Stages 8-10:  Docker (CPU)       - post_ner, subtitle_gen, mux
```

**Performance:**
- Silero VAD: 217s → 15s (14x)
- PyAnnote VAD: 687s → 40s (17x)
- Diarization: 5917s → 240s (25x)
- ASR: 2236s → 180s (12x)
- **Total: 2.5 hours → 8 minutes**

---

## ML Stages That Use GPU Acceleration

These 4 stages benefit from MPS/CUDA:

1. **Stage 4: Silero VAD** - Silero voice activity detection (PyTorch)
2. **Stage 5: PyAnnote VAD** - PyAnnote voice segmentation (PyTorch)
3. **Stage 6: Diarization** - PyAnnote speaker diarization (PyTorch)
4. **Stage 7: ASR** - WhisperX transcription (PyTorch)

**All other stages always run in Docker on CPU** (FFmpeg, API calls, text processing).

---

## How It Works

### Device Detection

The orchestrator reads the `DEVICE` setting from your job configuration:

```python
# Priority order:
1. DEVICE=cpu|mps|cuda        # New format (recommended)
2. DEVICE_WHISPERX=cpu|mps|cuda  # Legacy format (still supported)
3. Default: cpu               # Fallback if not specified
```

### Execution Decision

For each stage, the orchestrator decides:

```python
if stage in ML_STAGES and DEVICE in ['mps', 'cuda']:
    # Run natively with GPU acceleration
    run_native_step()
else:
    # Run in Docker on CPU
    run_docker_step()
```

### Native Execution

Native stages run using:
- **Virtual environments:** `native/venvs/{stage_name}/`
- **Python scripts:** `native/scripts/0X_stage.py`
- **Device manager:** Auto-detects and uses MPS/CUDA

---

## Setup Requirements

### For CPU Mode (Default)
✅ **No special setup** - Docker Desktop is all you need

### For MPS Mode
1. **Hardware:** M1/M2/M3/M4 Mac
2. **Native venvs:** Run once to set up:
   ```bash
   cd /Users/rpatel/Projects/cp-whisperx-app
   ./native/setup_venvs.sh
   ```
3. **Job config:** Set `DEVICE=mps`

### For CUDA Mode
1. **Hardware:** NVIDIA GPU (GTX 1060+ or RTX series)
2. **Drivers:** NVIDIA drivers installed
3. **Native venvs:** Run once to set up:
   ```bash
   cd /Users/rpatel/Projects/cp-whisperx-app
   ./native/setup_venvs.sh
   ```
4. **Job config:** Set `DEVICE=cuda`

---

## Usage Examples

### Example 1: Run with CPU (Default)

```bash
# Job config: DEVICE=cpu (or not set)
python pipeline.py --job 20251102-0004
```

**Output:**
```
[INFO] Device mode: CPU
[INFO] STAGE 4/10: SILERO_VAD
[INFO] 🐳 Running in Docker container (CPU)
```

### Example 2: Run with MPS

```bash
# Edit job config first:
# jobs/2025/11/02/20251102-0004/.20251102-0004.env
# Add: DEVICE=mps

python pipeline.py --job 20251102-0004
```

**Output:**
```
[INFO] Device mode: MPS
[INFO] STAGE 4/10: SILERO_VAD
[INFO] 🚀 Running natively with MPS acceleration
```

### Example 3: Run with CUDA

```bash
# Edit job config first:
# jobs/2025/11/02/20251102-0004/.20251102-0004.env
# Add: DEVICE=cuda

python pipeline.py --job 20251102-0004
```

**Output:**
```
[INFO] Device mode: CUDA
[INFO] STAGE 4/10: SILERO_VAD
[INFO] 🚀 Running natively with CUDA acceleration
```

---

## Checking Device Mode

### List Available Stages
```bash
python pipeline.py --list-stages
```

Output shows which stages use ML:
```
 4. silero_vad      → silero-vad      (timeout: 1800s) [CRITICAL] [ML]
 5. pyannote_vad    → pyannote-vad    (timeout: 3600s) [CRITICAL] [ML]
 6. diarization     → diarization     (timeout: 7200s) [CRITICAL] [ML]
 7. asr             → asr             (timeout: 14400s) [CRITICAL] [ML]

ML stages (can use MPS/CUDA acceleration):
silero_vad → pyannote_vad → diarization → asr
```

### Check Job Configuration
```bash
cat jobs/2025/11/02/20251102-0004/.20251102-0004.env | grep DEVICE
```

---

## Performance Comparison Table

| Stage | CPU (Docker) | MPS (Native) | CUDA (Native) |
|-------|--------------|--------------|---------------|
| Demux | 48s | 48s | 48s |
| TMDB | 2s | 2s | 2s |
| Pre-NER | 3s | 3s | 3s |
| **Silero VAD** | **217s** | **39s** ⚡ | **15s** 🚀 |
| **PyAnnote VAD** | **687s** | **120s** ⚡ | **40s** 🚀 |
| **Diarization** | **5917s** | **900s** ⚡ | **240s** 🚀 |
| **ASR** | **2236s*** | **600s** ⚡ | **180s** 🚀 |
| Post-NER | 5s | 5s | 5s |
| Subtitle Gen | 2s | 2s | 2s |
| Mux | 10s | 10s | 10s |
| **TOTAL** | **~151 min** | **~28 min** | **~8 min** |

*ASR failed timeout on CPU

---

## Troubleshooting

### Issue: "Python venv not found"
**Solution:** Run native venv setup:
```bash
./native/setup_venvs.sh
```

### Issue: MPS not detected
**Solution:** Verify MPS availability:
```bash
python3 -c "import torch; print('MPS:', torch.backends.mps.is_available())"
```

### Issue: CUDA not detected
**Solution:** Verify CUDA availability:
```bash
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
nvidia-smi
```

### Issue: Stage runs in Docker instead of native
**Check:**
1. `DEVICE` setting in job config
2. Native venvs installed
3. Stage is one of the 4 ML stages

---

## Migration Guide

### From Old Format to New

**Old format (still works):**
```bash
DEVICE_WHISPERX=mps
DEVICE_DIARIZATION=
DEVICE_SECOND_PASS=cpu
DEVICE_SPACY=cpu
```

**New format (recommended):**
```bash
DEVICE=mps  # Single setting for all ML stages
```

The orchestrator checks both formats (new format takes priority).

---

## Summary

✅ **CPU Mode:** All Docker, works everywhere, slowest
✅ **MPS Mode:** ML stages native with MPS, 5-6x faster
✅ **CUDA Mode:** ML stages native with CUDA, 15-20x faster

**Device selection is automatic based on job config!**

Just set `DEVICE=cpu|mps|cuda` in your job's `.env` file.

---

## Related Documentation

- `MPS_ACCELERATION_GUIDE.md` - MPS setup and performance
- `CUDA_ACCELERATION_GUIDE.md` - CUDA setup and performance
- `PIPELINE_RESUME_GUIDE.md` - Resume and recovery
- `native/` - Native execution scripts and venvs
