# CP-WhisperX-App Comprehensive Test Plan

## Test Matrix Overview

| Platform | Device | Mode | Priority | Status |
|----------|--------|------|----------|--------|
| macOS | MPS | Native | HIGH | ⏳ |
| macOS | CPU | Docker | MEDIUM | ⏳ |
| Linux | CUDA | Docker | HIGH | ⏳ |
| Linux | CPU | Docker | MEDIUM | ⏳ |
| Windows | CUDA | Docker | HIGH | ⏳ |
| Windows | CPU | Docker | MEDIUM | ⏳ |

## Prerequisites Checklist

### All Platforms
- [ ] Python 3.11+ installed
- [ ] Docker Desktop installed and running
- [ ] Git repository cloned
- [ ] Config file setup (`config/.env.pipeline`)
- [ ] TMDB API key configured
- [ ] HuggingFace token configured
- [ ] Test video file available (recommend: 5-10 min clip)

### macOS Specific
- [ ] Apple Silicon Mac (M1/M2/M3)
- [ ] Native venvs created (`./native/setup_venvs.sh`)
- [ ] PyTorch MPS support verified

### Linux Specific  
- [ ] NVIDIA GPU available
- [ ] NVIDIA drivers installed (`nvidia-smi` works)
- [ ] NVIDIA Container Toolkit installed
- [ ] Docker GPU support verified

### Windows Specific
- [ ] NVIDIA GPU available
- [ ] WSL2 enabled
- [ ] Docker Desktop with WSL2 backend
- [ ] NVIDIA drivers in WSL2
- [ ] NVIDIA Container Toolkit in WSL2

---

## Test Suite 1: Basic Functionality

### Test 1.1: Job Preparation
**Purpose:** Verify job creation and configuration

```bash
# Test command
python prepare-job.py /path/to/test-video.mp4

# Expected output
✓ Job created: YYYYMMDD-NNNN
✓ Directory: out/YYYY/MM/DD/1/YYYYMMDD-NNNN
✓ Job definition: .../job.json
```

**Checklist:**
- [ ] Job ID generated correctly (YYYYMMDD-NNNN format)
- [ ] Job directory created in correct location
- [ ] `job.json` file created with metadata
- [ ] `.env` file generated from template
- [ ] Media file copied/linked to job directory
- [ ] No errors in output

**Validation:**
```bash
# Check job.json
cat out/.../job.json | jq .

# Check .env
cat out/.../.<job-id>.env | grep JOB_ID
```

---

### Test 1.2: Clip Creation
**Purpose:** Verify media clipping for testing

```bash
# Test command
python prepare-job.py /path/to/test-video.mp4 \
  --start-time 00:10:00 \
  --end-time 00:15:00
```

**Checklist:**
- [ ] Clip created successfully
- [ ] Duration is approximately 5 minutes
- [ ] job.json shows `is_clip: true`
- [ ] clip_start and clip_end recorded
- [ ] Video quality maintained

**Validation:**
```bash
ffprobe out/.../test-video_clip_*.mp4 2>&1 | grep Duration
```

---

### Test 1.3: Configuration Template
**Purpose:** Verify config template processing

```bash
# Test command
python prepare-job.py test-video.mp4 --transcribe --native
```

**Checklist:**
- [ ] Template `config/.env.pipeline` read successfully
- [ ] Job-specific values injected (JOB_ID, IN_ROOT, OUTPUT_ROOT)
- [ ] Workflow mode set correctly (WORKFLOW_MODE=transcribe)
- [ ] Native mode device detected and set
- [ ] Stage enable/disable flags set correctly

**Validation:**
```bash
cat out/.../.<job-id>.env | grep -E "WORKFLOW_MODE|DEVICE|STEP_"
```

---

## Test Suite 2: Docker Mode Testing

### Test 2.1: Docker - CPU Mode (All Platforms)
**Purpose:** Verify Docker execution without GPU

```bash
# Prepare job (no --native flag)
python prepare-job.py test-video.mp4 --transcribe

# Run pipeline
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] Pipeline starts successfully
- [ ] All stages run in Docker containers
- [ ] No GPU flags used (--gpus)
- [ ] CPU resources used
- [ ] demux stage completes
- [ ] silero-vad stage completes  
- [ ] asr stage completes
- [ ] transcript.txt generated
- [ ] Logs created for each stage
- [ ] manifest.json updated

**Expected Duration:** 15-30 minutes for 5-min clip

**Validation:**
```bash
# Check transcript
cat out/.../transcription/transcript.txt

# Check logs
ls -lh out/.../logs/

# Check manifest
cat out/.../manifest.json | jq '.pipeline.completed_stages'
```

---

### Test 2.2: Docker - Full Pipeline (CPU)
**Purpose:** Verify complete subtitle generation

```bash
python prepare-job.py test-video.mp4
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] All stages execute in order
- [ ] demux → tmdb → pre-ner → silero-vad → pyannote-vad
- [ ] diarization → asr → post-ner → subtitle-gen → mux
- [ ] Subtitle file (.srt) created
- [ ] Final video with subtitles created
- [ ] No stage failures
- [ ] Pipeline completes successfully

**Expected Duration:** 30-60 minutes for 5-min clip

**Validation:**
```bash
# Check subtitle file
cat out/.../subtitles/*.srt | head -20

# Check final video
ls -lh out/.../subtitles/*_with_subtitles.mkv
```

---

## Test Suite 3: Native Mode Testing (macOS)

### Test 3.1: Native MPS - Transcription Only
**Purpose:** Verify native execution with MPS GPU

**Prerequisites:**
```bash
./native/setup_venvs.sh
```

**Test:**
```bash
python prepare-job.py test-video.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] Device detected as MPS
- [ ] Log shows "Running natively with MPS GPU acceleration"
- [ ] ML stages use native venvs
- [ ] Non-ML stages use Docker
- [ ] demux (Docker) completes
- [ ] silero-vad (Native) completes
- [ ] asr (Native) completes
- [ ] Faster than CPU mode
- [ ] GPU utilization visible in Activity Monitor

**Expected Duration:** 5-15 minutes for 5-min clip

**Validation:**
```bash
# Check device in logs
grep "Device mode" out/.../logs/orchestrator_*.log

# Check execution mode
grep "Running natively" out/.../logs/orchestrator_*.log
```

---

### Test 3.2: Native MPS - Full Pipeline
**Purpose:** Verify full subtitle pipeline with MPS

```bash
python prepare-job.py test-video.mp4 --native
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] ML stages run natively (silero-vad, pyannote-vad, diarization, asr)
- [ ] Non-ML stages run in Docker
- [ ] Pipeline completes successfully
- [ ] Subtitles generated correctly
- [ ] Performance better than Docker-only

**Expected Duration:** 10-25 minutes for 5-min clip

---

## Test Suite 4: CUDA Mode Testing (Linux/Windows)

### Test 4.1: CUDA Docker - Transcription
**Purpose:** Verify Docker with GPU passthrough

**Prerequisites:**
```bash
# Verify GPU
nvidia-smi

# Verify Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**Test:**
```bash
python prepare-job.py test-video.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] Device detected as CUDA
- [ ] Log shows "Running in Docker with CUDA GPU support"
- [ ] Docker containers use --gpus all flag
- [ ] GPU utilization visible (nvidia-smi)
- [ ] Faster than CPU mode
- [ ] transcript.txt generated

**Expected Duration:** 5-15 minutes for 5-min clip

**Validation:**
```bash
# Check GPU usage during run
watch -n 1 nvidia-smi

# Check logs for CUDA
grep "CUDA" out/.../logs/orchestrator_*.log
```

---

### Test 4.2: CUDA Docker - Full Pipeline
**Purpose:** Complete subtitle generation with CUDA

```bash
python prepare-job.py test-video.mp4 --native
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] All ML stages use CUDA Docker containers
- [ ] GPU memory utilization visible
- [ ] All stages complete successfully
- [ ] Performance significantly better than CPU
- [ ] Subtitles quality is good

**Expected Duration:** 10-25 minutes for 5-min clip

---

## Test Suite 5: Resume and Error Handling

### Test 5.1: Pipeline Resume
**Purpose:** Verify resume after interruption

```bash
# Start pipeline
python pipeline.py --job <job-id>

# Stop after 2-3 stages (Ctrl+C)

# Resume
python pipeline.py --job <job-id> --resume
```

**Checklist:**
- [ ] Pipeline detects completed stages
- [ ] Skips already-completed stages
- [ ] Resumes from next stage
- [ ] Completes successfully
- [ ] No duplicate work

**Validation:**
```bash
# Check manifest before resume
cat out/.../manifest.json | jq '.pipeline.completed_stages'

# Check logs show skipped stages
grep "Skipping" out/.../logs/orchestrator_*.log
```

---

### Test 5.2: Stage-Specific Execution
**Purpose:** Run specific stages only

```bash
python pipeline.py --job <job-id> --stages asr
```

**Checklist:**
- [ ] Only requested stage runs
- [ ] Other stages skipped
- [ ] Stage completes successfully
- [ ] Useful for debugging

---

### Test 5.3: Error Recovery
**Purpose:** Verify error handling

**Test scenarios:**
- [ ] Missing config file
- [ ] Invalid job ID
- [ ] Missing API key
- [ ] Network timeout
- [ ] Out of disk space
- [ ] Stage failure

**Expected behavior:**
- [ ] Clear error message
- [ ] Logs show error details
- [ ] manifest.json shows failure
- [ ] Can resume after fixing issue

---

## Test Suite 6: Multi-User Testing

### Test 6.1: Different USER_IDs
**Purpose:** Verify multi-user support

```bash
# User 1
export USER_ID=1
python prepare-job.py test1.mp4
# Expected: out/YYYY/MM/DD/1/YYYYMMDD-NNNN/

# User 2
export USER_ID=2
python prepare-job.py test2.mp4
# Expected: out/YYYY/MM/DD/2/YYYYMMDD-NNNN/
```

**Checklist:**
- [ ] Jobs isolated by USER_ID
- [ ] No conflicts between users
- [ ] Each user has own directory
- [ ] Job numbering independent per user

---

## Test Suite 7: Workflow Modes

### Test 7.1: Transcribe Workflow
**Purpose:** Simplified workflow

```bash
python prepare-job.py test.mp4 --transcribe
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] Only demux → silero-vad → asr stages run
- [ ] Diarization skipped
- [ ] Subtitle-gen skipped
- [ ] Mux skipped
- [ ] Faster completion
- [ ] transcript.txt created

---

### Test 7.2: Subtitle-Gen Workflow
**Purpose:** Full workflow (default)

```bash
python prepare-job.py test.mp4
python pipeline.py --job <job-id>
```

**Checklist:**
- [ ] All stages run
- [ ] Subtitles created
- [ ] Final video with subtitles

---

## Performance Benchmarks

### Baseline (5-minute clip):

| Platform | Device | Mode | Time | Notes |
|----------|--------|------|------|-------|
| macOS M1 | MPS | Native | ~10min | Best macOS performance |
| macOS M1 | CPU | Docker | ~25min | Baseline |
| Linux | RTX 3090 | Docker+CUDA | ~8min | Best overall |
| Linux | CPU | Docker | ~30min | Slowest |
| Windows | RTX 4080 | Docker+CUDA | ~9min | Good performance |

*Actual times vary based on hardware, video complexity, and model size*

---

## Success Criteria

### Must Pass:
- ✅ All Test Suite 1 (Basic Functionality)
- ✅ Test 2.1 (Docker CPU) on all platforms
- ✅ Test 3.1 (Native MPS) on macOS
- ✅ Test 4.1 (CUDA) on Linux/Windows
- ✅ Test 5.1 (Resume)

### Should Pass:
- ✅ Full pipeline tests (2.2, 3.2, 4.2)
- ✅ Multi-user tests
- ✅ Workflow mode tests

### Nice to Have:
- ✅ Performance meets benchmarks
- ✅ Error handling graceful
- ✅ Logs are clear and helpful

---

## Reporting Issues

When reporting test failures, include:

1. **Platform**: macOS/Linux/Windows
2. **Device**: MPS/CUDA/CPU
3. **Mode**: Native/Docker
4. **Test**: Suite and test number
5. **Command**: Exact command run
6. **Error**: Error message
7. **Logs**: Relevant log excerpts
8. **Job ID**: For reference

**Template:**
```
Platform: macOS M1
Device: MPS  
Mode: Native
Test: 3.1 - Native MPS Transcription
Command: python pipeline.py --job 20251103-0001
Error: Stage failed: asr
Logs: [attach orchestrator_*.log and asr_*.log]
Job ID: 20251103-0001
```

---

## Test Execution Tracking

Copy this section for each test run:

```
Date: _______________
Tester: _______________
Platform: _______________

Test Suite 1: Basic Functionality
[ ] 1.1 Job Preparation
[ ] 1.2 Clip Creation  
[ ] 1.3 Configuration Template

Test Suite 2: Docker Mode
[ ] 2.1 Docker CPU
[ ] 2.2 Docker Full Pipeline

Test Suite 3: Native Mode (macOS)
[ ] 3.1 Native MPS Transcription
[ ] 3.2 Native MPS Full Pipeline

Test Suite 4: CUDA Mode (Linux/Windows)
[ ] 4.1 CUDA Transcription
[ ] 4.2 CUDA Full Pipeline

Test Suite 5: Resume/Error
[ ] 5.1 Pipeline Resume
[ ] 5.2 Stage-Specific
[ ] 5.3 Error Recovery

Test Suite 6: Multi-User
[ ] 6.1 Different USER_IDs

Test Suite 7: Workflows
[ ] 7.1 Transcribe Workflow
[ ] 7.2 Subtitle-Gen Workflow

Notes:
_________________________________
_________________________________
_________________________________
```
