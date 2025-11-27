# WhisperX 3.7.4 Upgrade Guide

**Date:** 2024-11-20  
**Question:** Can we use latest whisperx 3.7.4 with torch 2.8.0 in multi-environment architecture?

## Answer: YES! ✅

Thanks to our **multi-environment isolation**, we can safely upgrade `venv/whisperx` to use the latest versions without affecting other environments.

## Architecture Benefits

### Environment Isolation

Each environment is **completely independent**:

| Environment | PyTorch | NumPy | Purpose | Stages |
|-------------|---------|-------|---------|--------|
| `venv/common` | - | - | Core utilities | job prep, logging, mux |
| `venv/whisperx` | 2.0.0 → **2.8.0** | <2.0 → **≥2.0.2** | WhisperX ASR | demux, asr, alignment |
| `venv/mlx` | 2.9.1 | <2.0 | MLX acceleration | asr (Apple Silicon) |
| `venv/indictrans2` | ≥2.5.0 | ≥2.1.0 | Translation | translation |

**Key Point:** Upgrading `venv/whisperx` does NOT affect `venv/indictrans2` or `venv/mlx`!

## Affected Stages

### Only 3 Stages Use `venv/whisperx`:

1. **demux** - Audio/video extraction
   - Extracts audio from video files
   - Uses FFmpeg (via ffmpeg-python)
   - Risk: Low (minimal torch usage)

2. **asr** - Automatic Speech Recognition
   - Transcribes audio using WhisperX
   - Uses torch models heavily
   - Risk: Medium (core functionality)

3. **alignment** - Word-level timestamp alignment
   - Aligns words with audio timestamps
   - Uses WhisperX alignment models
   - Risk: Medium (torch model inference)

### Unaffected Stages:

- **translation** - Uses `venv/indictrans2` (already torch 2.5+)
- **subtitle_gen** - Uses `venv/common` (no ML)
- **mux** - Uses `venv/common` (no ML)
- **asr (MLX mode)** - Uses `venv/mlx` (separate torch)

## Upgrade Changes

### requirements-whisperx.txt

```diff
 # WhisperX Environment Requirements
-# Compatible with torch ~=2.0.0 and numpy <2.0.0
+# Compatible with torch ~=2.8.0 and numpy >=2.0.2

 # Core WhisperX with dependencies
-# Using 3.3.1 (latest compatible with torch 2.0.x)
-whisperx==3.3.1
+# Using 3.7.4 (latest version with torch 2.8.x)
+whisperx==3.7.4

 # PyTorch ecosystem
-torch~=2.0.0
-torchaudio~=2.0.0
-numpy>=1.23.0,<2.0.0
+torch~=2.8.0
+torchaudio~=2.8.0
+numpy>=2.0.2,<2.1.0
```

## Breaking Changes Analysis

### 1. PyTorch 2.0 → 2.8 Changes

**API Changes:**
- `torch.jit` improvements
- Better MPS backend (macOS Metal)
- CUDA 12 support
- Performance optimizations

**Impact:**
- Low - WhisperX abstracts most torch APIs
- May see performance improvements on Apple Silicon

### 2. NumPy 1.x → 2.0 Changes

**Breaking Changes:**
- Type system overhaul
- Array API standardization
- Removed deprecated functions

**Impact:**
- Low - whisperx 3.7.4 is designed for numpy 2.0
- Dependencies updated to handle changes

### 3. Dependency Compatibility

**pyannote.audio:**
- 3.1.1 (current) → 3.3.2+ (whisperx 3.7.4 requires)
- Compatible with torch 2.8 ✅

**faster-whisper:**
- 1.0.0+ (current) → 1.1.1+ (whisperx 3.7.4 requires)
- Compatible with torch 2.8 ✅

## Implementation Steps

### Option A: Upgrade Now (Recommended for Development)

```bash
# 1. Update requirements file
cat > requirements-whisperx.txt << 'EOF'
# WhisperX Environment Requirements
# Compatible with torch ~=2.8.0 and numpy >=2.0.2

# Core WhisperX with dependencies
whisperx==3.7.4

# PyTorch ecosystem (latest versions)
torch~=2.8.0
torchaudio~=2.8.0
numpy>=2.0.2,<2.1.0

# Faster Whisper backend (CTranslate2)
faster-whisper>=1.1.1

# Audio/Video processing
ffmpeg-python>=0.2.0

# Utilities
python-dotenv>=1.0.0
EOF

# 2. Recreate whisperx environment
rm -rf venv/whisperx
./bootstrap.sh

# 3. Test with small file
./prepare-job.sh in/test-short.mp4 --transcribe -s hi --debug
./run-pipeline.sh -j <job-id>

# 4. Check logs for errors
tail -100 out/*/logs/06_asr_*.log

# 5. Verify output
cat out/*/transcripts/transcript_source.txt
```

### Option B: Stay on 3.3.1 (Recommended for Production)

```bash
# No changes needed - current stable version
# Keep requirements-whisperx.txt as-is
```

## Testing Checklist

### Basic Functionality

- [ ] Bootstrap completes without errors
- [ ] Environment creation succeeds
- [ ] No dependency conflicts

### Stage Testing

- [ ] **demux**: Extracts audio from video
  ```bash
  # Test audio extraction
  ls out/<job>/audio/
  ffprobe out/<job>/audio/audio.wav
  ```

- [ ] **asr**: Transcribes audio correctly
  ```bash
  # Check transcript exists and has content
  cat out/<job>/transcripts/transcript_source.txt
  # Should contain Hindi text if source was Hindi
  ```

- [ ] **alignment**: Word timestamps accurate
  ```bash
  # Check word-level JSON
  cat out/<job>/alignment/aligned_segments.json | jq '.segments[0]'
  ```

### Integration Testing

- [ ] **Full transcribe workflow**
  ```bash
  ./prepare-job.sh in/movie.mp4 --transcribe -s hi
  ./run-pipeline.sh -j <job-id>
  ```

- [ ] **Full subtitle workflow**
  ```bash
  ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en
  ./run-pipeline.sh -j <job-id>
  ```

- [ ] **Clipping functionality**
  ```bash
  ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
      --start-time 00:05:00 --end-time 00:10:00
  ./run-pipeline.sh -j <job-id>
  ```

### Performance Testing

- [ ] Compare transcription speed (3.3.1 vs 3.7.4)
- [ ] Check memory usage
- [ ] Validate GPU utilization (if applicable)

## Rollback Procedure

If issues are found:

```bash
# 1. Restore original requirements
git checkout requirements-whisperx.txt

# 2. Remove upgraded environment
rm -rf venv/whisperx

# 3. Recreate with stable version
./bootstrap.sh

# 4. Verify rollback
venv/whisperx/bin/python -c "import whisperx; print(whisperx.__version__)"
# Should show: 3.3.1
```

## Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| torch 2.8 API breaks | Medium | Low | Test all stages, easy rollback |
| numpy 2.0 compatibility | Low | Very Low | whisperx 3.7.4 designed for it |
| Performance regression | Low | Very Low | Benchmark before/after |
| Transcription accuracy | Medium | Very Low | Compare outputs |
| Environment corruption | Very Low | Very Low | Isolated, recreate easily |

**Overall Risk: LOW** ✅

## Benefits of Upgrading

### 1. Latest Features
- Improved transcription accuracy
- Better timestamp alignment
- Enhanced language support

### 2. Performance
- Optimized torch 2.8 backend
- Better GPU utilization
- Faster inference on Apple Silicon

### 3. Security
- Latest security patches
- Updated dependencies
- No yanked packages

### 4. Maintenance
- Official supported version
- Active development
- Bug fixes

## Decision Matrix

### Upgrade to 3.7.4 if:
- ✅ You're testing in development
- ✅ You have time to validate
- ✅ You want latest features
- ✅ You're on macOS M-series (MPS improvements)
- ✅ Your production pipeline has test coverage

### Stay on 3.3.1 if:
- ✅ Production stability is critical
- ✅ No time for testing
- ✅ Current version works perfectly
- ✅ Risk-averse deployment policy

## Monitoring After Upgrade

### Key Metrics to Watch

1. **Transcription Accuracy**
   - Compare WER (Word Error Rate)
   - Spot-check 10-20 samples
   - Verify punctuation/capitalization

2. **Performance**
   - Transcription time per minute of audio
   - Memory usage
   - GPU utilization

3. **Stability**
   - Error rates
   - Pipeline failures
   - Stage crashes

4. **Output Quality**
   - Timestamp precision
   - Alignment accuracy
   - Missing/extra words

## Recommendation

### For Development: ✅ UPGRADE

**Rationale:**
- Safe to test thanks to isolation
- Easy rollback if issues found
- Benefits likely outweigh risks
- Future-proofs the codebase

### For Production: ⏸️ WAIT

**Rationale:**
- Test thoroughly in dev first
- Validate on representative data
- Monitor for 1-2 weeks
- Then promote to production

## Summary

**Can we upgrade?** YES ✅

**Affected stages:** demux, asr, alignment (only `venv/whisperx`)

**Breaking changes:** Contained within isolated environment

**Risk level:** LOW

**Recommendation:** Upgrade in dev, test thoroughly, then deploy to production

**Rollback time:** < 5 minutes

The multi-environment architecture makes this upgrade **safe and reversible**! 🎉
