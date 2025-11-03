# CP-WhisperX-App Test Plan

Comprehensive testing and validation checklist for the CP-WhisperX-App pipeline.

---

## Pre-Deployment Validation

### 1. System Requirements Check

#### Hardware Validation
- [ ] **RAM:** 16GB+ available
- [ ] **Storage:** 20GB+ free space
- [ ] **GPU:** CUDA/MPS device detected (if applicable)
- [ ] **CPU:** 4+ cores available

#### Software Dependencies
- [ ] **Python:** 3.9+ installed
- [ ] **FFmpeg:** Latest version installed
- [ ] **Docker:** Latest version (for Docker mode)
- [ ] **Git:** Installed and configured

#### Command:
```bash
python preflight.py
```

**Expected Output:**
- All checks pass with green checkmarks
- GPU detected (if available)
- Virtual environments created successfully

---

### 2. Configuration Validation

#### Environment Files
- [ ] `config/.env` exists with valid settings
- [ ] `config/secrets.json` exists (if using)
- [ ] `HF_TOKEN` set (for diarization)
- [ ] `TMDB_API_KEY` set (optional)
- [ ] Device setting appropriate (`auto`, `cuda`, `mps`, or `cpu`)

#### API Access
```bash
# Test TMDB API
python native/scripts/test_tmdb.py

# Test PyAnnote access
python native/scripts/test_pyannote_vad.py
```

**Expected Output:**
- TMDB: Movie data retrieved successfully
- PyAnnote: Model loaded without errors

---

### 3. GPU Detection Validation

#### Test GPU Recognition
```bash
python preflight.py --check-device
```

**Expected Output:**
- **CUDA:** Device name, compute capability, VRAM
- **MPS:** Apple Silicon detected
- **CPU:** CPU fallback mode active

#### Verify Device Selection
```bash
# In config/.env:
DEVICE=auto

# Or override:
python prepare-job.py test.mp4 --native --device cuda
```

---

## Functional Testing

### 4. Transcribe Workflow Tests

#### 4.1 Basic Transcribe (Short Clip)
```bash
# Prepare 2-minute test clip
python prepare-job.py test_short.mp4 --transcribe --native --clip-duration 120

# Run pipeline
python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] Job created successfully
- [ ] Stages execute in order: demux → VAD → ASR
- [ ] No errors in logs
- [ ] Transcript file created: `out/<date>/<job-id>/transcript/transcript.txt`
- [ ] Transcript contains readable text
- [ ] Processing time reasonable (< 5 minutes with GPU)

#### 4.2 Full Transcribe (Long Video)
```bash
python prepare-job.py test_full.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] All stages complete successfully
- [ ] Memory usage stays within limits
- [ ] Transcript quality is good
- [ ] Processing time reasonable (~10-15 min for 2-hour video with GPU)

---

### 5. Subtitle Generation Workflow Tests

#### 5.1 Basic Subtitle Gen (Short Clip)
```bash
python prepare-job.py test_short.mp4 --subtitle-gen --native --clip-duration 120
python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] All 12 stages execute successfully
- [ ] TMDB metadata fetched (if API key provided)
- [ ] Pre-NER entities extracted
- [ ] VAD stages complete (Silero + PyAnnote)
- [ ] Diarization identifies speakers
- [ ] ASR transcription accurate
- [ ] Second pass translation runs
- [ ] Lyrics detection completes
- [ ] Post-NER corrections applied
- [ ] SRT subtitle file created
- [ ] Output video with embedded subtitles generated
- [ ] Subtitles display correctly in video player

#### 5.2 Full Subtitle Gen (Long Video)
```bash
python prepare-job.py test_full.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] Complete pipeline execution (30-45 min with GPU)
- [ ] All output files present
- [ ] Subtitle timing accurate
- [ ] Speaker labels correct
- [ ] Entity names properly corrected
- [ ] Video quality preserved
- [ ] Subtitles readable and well-formatted

---

### 6. Docker Mode Tests

#### 6.1 Docker Image Build
```bash
cd docker
./scripts/build-images.sh
```

**Validation Checklist:**
- [ ] Base image builds successfully
- [ ] All stage images build without errors
- [ ] Images tagged correctly
- [ ] No security vulnerabilities reported

#### 6.2 Docker Workflow Execution
```bash
python prepare-job.py test.mp4 --subtitle-gen --docker
python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] Docker containers start successfully
- [ ] Volumes mount correctly
- [ ] Stages execute in containers
- [ ] Output artifacts accessible on host
- [ ] Containers clean up properly

---

### 7. Resume Capability Tests

#### 7.1 Simulated Failure Recovery
```bash
# Start pipeline
python pipeline.py --job <job-id>

# Stop manually at mid-stage (Ctrl+C)

# Resume
./resume-pipeline.sh <job-id>
```

**Validation Checklist:**
- [ ] Pipeline detects last completed stage
- [ ] Resumes from correct stage
- [ ] No duplicate processing
- [ ] Manifest updated correctly
- [ ] Final output complete

#### 7.2 Stage Failure Handling
```bash
# Introduce intentional error (e.g., remove HF token)
# Run pipeline
python pipeline.py --job <job-id>

# Fix error
# Resume
./resume-pipeline.sh <job-id>
```

**Validation Checklist:**
- [ ] Error logged clearly
- [ ] Pipeline stops at failed stage
- [ ] Resume starts from failed stage
- [ ] Successful completion after fix

---

### 8. Cross-Platform Tests

#### 8.1 Windows 11 Pro (CUDA)
```powershell
# Run full test suite
python preflight.py
python prepare-job.py test.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Platform-Specific Checks:**
- [ ] CUDA GPU detected
- [ ] Windows paths handled correctly
- [ ] Batch scripts work (`.bat` files)
- [ ] FFmpeg runs without issues
- [ ] Output files accessible

#### 8.2 macOS (Apple Silicon MPS)
```bash
# Run full test suite
python preflight.py
python prepare-job.py test.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Platform-Specific Checks:**
- [ ] MPS device detected
- [ ] Metal acceleration active
- [ ] Virtual environments created correctly
- [ ] Shell scripts execute (`.sh` files)
- [ ] No permission issues

#### 8.3 Linux (CUDA)
```bash
# Run full test suite
python preflight.py
python prepare-job.py test.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Platform-Specific Checks:**
- [ ] CUDA GPU detected
- [ ] cuDNN libraries available
- [ ] Permissions correct
- [ ] Docker works (if testing Docker mode)

---

### 9. Performance Tests

#### 9.1 GPU Utilization
```bash
# Monitor GPU during pipeline
watch -n 1 nvidia-smi  # CUDA
sudo powermetrics --samplers gpu_power  # MPS

python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] GPU utilization > 80% during ML stages
- [ ] VRAM usage within limits
- [ ] No GPU memory leaks
- [ ] Temperature stays safe

#### 9.2 Memory Usage
```bash
# Monitor memory during pipeline
htop  # or top

python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] RAM usage < 80% of available
- [ ] No memory leaks
- [ ] Garbage collection working
- [ ] Virtual environments isolated

#### 9.3 Processing Speed Benchmarks
Test with 2-hour movie:

| Workflow      | Expected Time (GPU) | Expected Time (CPU) |
|---------------|---------------------|---------------------|
| Transcribe    | 10-15 min           | 2-3 hrs            |
| Subtitle-Gen  | 30-45 min           | 5-8 hrs            |

**Validation:**
- [ ] Times within expected ranges
- [ ] GPU mode significantly faster than CPU

---

### 10. Output Quality Tests

#### 10.1 Transcript Quality
**Check for:**
- [ ] Accurate transcription (< 5% word error rate)
- [ ] Proper punctuation
- [ ] Correct language detection
- [ ] No garbled text
- [ ] Timestamps accurate

#### 10.2 Subtitle Quality
**Check for:**
- [ ] Proper SRT formatting
- [ ] Accurate timing (sync with audio)
- [ ] Readable line lengths (< 42 characters)
- [ ] Correct speaker labels
- [ ] Entity names properly formatted
- [ ] No overlapping subtitles
- [ ] Smooth transitions

#### 10.3 Video Output Quality
**Check for:**
- [ ] Video quality preserved
- [ ] Audio sync maintained
- [ ] Subtitles embedded correctly
- [ ] Playback smooth in multiple players (VLC, MPV, etc.)
- [ ] File size reasonable

---

### 11. Edge Case Tests

#### 11.1 No Speech Detection
```bash
# Test with video containing no speech
python prepare-job.py silent.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] Pipeline completes without errors
- [ ] Empty or minimal transcript
- [ ] Graceful handling

#### 11.2 Single Speaker
```bash
# Test with single speaker video
python prepare-job.py monologue.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] Diarization detects single speaker
- [ ] Subtitles labeled correctly
- [ ] No speaker confusion

#### 11.3 Multiple Languages
```bash
# Test with code-switching (Hindi-English mix)
python prepare-job.py mixed_lang.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] Both languages transcribed
- [ ] Translation handles code-switching
- [ ] Entity names preserved

#### 11.4 Background Music/Noise
```bash
# Test with noisy audio
python prepare-job.py noisy.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] Speech extracted from noise
- [ ] VAD filters background sounds
- [ ] Acceptable transcription quality

---

### 12. Logging and Monitoring Tests

#### 12.1 Log File Creation
```bash
python pipeline.py --job <job-id>
```

**Validation Checklist:**
- [ ] Main pipeline log created: `logs/pipeline.log`
- [ ] Stage logs created: `logs/<stage>.log`
- [ ] Job-specific logs: `out/<date>/<job-id>/logs/`
- [ ] Log rotation working
- [ ] No sensitive data in logs

#### 12.2 Manifest Tracking
```bash
# Check manifest after pipeline
cat out/<date>/<job-id>/manifest.json
```

**Validation Checklist:**
- [ ] All stages recorded
- [ ] Timestamps accurate
- [ ] Input/output files listed
- [ ] Status correct (completed/failed)
- [ ] Metadata preserved

---

### 13. Error Handling Tests

#### 13.1 Missing Dependencies
```bash
# Temporarily rename FFmpeg
# Run pipeline
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] Clear error message
- [ ] Pipeline stops gracefully
- [ ] Suggestion to install FFmpeg

#### 13.2 Invalid Input
```bash
# Test with corrupt/invalid video
python prepare-job.py corrupt.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] Error detected at demux stage
- [ ] Clear error message
- [ ] No partial artifacts

#### 13.3 API Failures
```bash
# Test with invalid TMDB key
python pipeline.py --job <job-id>
```

**Expected:**
- [ ] TMDB stage fails gracefully
- [ ] Pipeline continues without metadata
- [ ] Warning logged

---

## Regression Testing Checklist

After any code changes, verify:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Quick smoke test completes (2-min clip)
- [ ] Full workflow test completes
- [ ] No new warnings in logs
- [ ] Performance not degraded
- [ ] Documentation updated
- [ ] Changelog updated

---

## Deployment Checklist

Before pushing to production:

- [ ] All tests passed
- [ ] Documentation complete and accurate
- [ ] Configuration templates updated
- [ ] Example files provided
- [ ] Platform-specific guides verified
- [ ] Docker images built and pushed
- [ ] Release notes prepared
- [ ] Backup and rollback plan ready

---

## Continuous Testing

### Daily Smoke Tests
```bash
# Quick validation (5 minutes)
./scripts/tests/smoke_test.sh
```

### Weekly Full Tests
```bash
# Comprehensive validation (1-2 hours)
./scripts/tests/full_test.sh
```

### Pre-Release Tests
```bash
# Complete test suite (4-8 hours)
./scripts/tests/regression_test.sh
```

---

## Known Issues and Workarounds

### Issue: PyAnnote Model Download Slow
**Workaround:** Pre-download models to cache
```bash
python -c "from pyannote.audio import Model; Model.from_pretrained('pyannote/speaker-diarization-3.1')"
```

### Issue: FFmpeg Not in PATH (Windows)
**Workaround:** Add FFmpeg to system PATH or use full path in config

### Issue: Out of Memory on Long Videos
**Workaround:** Use `--clip-duration` or CPU mode
```bash
python prepare-job.py video.mp4 --native --device cpu
```

---

## Test Data

### Recommended Test Files

1. **Short Clip (2 min):** Quick validation
   - Single speaker
   - Clear audio
   - Simple content

2. **Medium Clip (10 min):** Intermediate test
   - 2-3 speakers
   - Some background noise
   - Mix of dialogue and narration

3. **Full Movie (2 hours):** Stress test
   - Multiple speakers
   - Songs/music
   - Various audio conditions
   - Code-switching (Hindi-English)

### Test File Requirements
- **Format:** MP4, MKV, or AVI
- **Audio:** AAC or MP3, 48kHz recommended
- **Video:** H.264 or H.265
- **Size:** Varied (100MB to 4GB)

---

## Success Criteria

A successful deployment must:

1. ✅ Pass all validation tests
2. ✅ Complete both workflows without errors
3. ✅ Produce high-quality output
4. ✅ Perform within expected time ranges
5. ✅ Handle errors gracefully
6. ✅ Work on all supported platforms
7. ✅ Resume from failures correctly
8. ✅ Log appropriately
9. ✅ Use resources efficiently
10. ✅ Be documented completely

---

**Test Status:** 🟢 All systems operational | 🟡 Minor issues | 🔴 Critical issues

**Last Tested:** [Date]  
**Tested By:** [Name]  
**Environment:** [Platform/GPU]  
**Result:** [Pass/Fail]
