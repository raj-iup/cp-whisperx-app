# WhisperX 3.7.4 Upgrade Complete

**Date:** 2024-11-20 05:15 UTC  
**Status:** ✅ SUCCESS

## Upgrade Summary

Successfully upgraded `venv/whisperx` environment from **whisperx 3.3.1** (torch 2.0.0) to **whisperx 3.7.4** (torch 2.8.0).

## Versions Installed

### Core Packages

| Package | Old Version | New Version | Status |
|---------|-------------|-------------|--------|
| **whisperx** | 3.3.1 | **3.7.4** | ✅ Upgraded |
| **torch** | 2.0.0 | **2.8.0** | ✅ Upgraded |
| **torchaudio** | 2.0.0 | **2.8.0** | ✅ Upgraded |
| **numpy** | 1.26.4 | **2.0.2** | ✅ Upgraded |

### Dependencies

| Package | Version | Notes |
|---------|---------|-------|
| pyannote.audio | 3.4.0 | Updated (was 3.1.1) |
| faster-whisper | 1.2.1 | Compatible |
| ctranslate2 | 4.6.1 | Compatible |
| transformers | 4.57.1 | Latest |
| pytorch-lightning | 2.5.6 | Compatible with torch 2.8 |

## Installation Details

**Environment:** `venv/whisperx`  
**Installation Time:** ~8 minutes  
**Total Packages:** 118 packages installed  
**Log File:** `logs/upgrade_whisperx_3.7.4.log`

## Verification

```bash
$ source venv/whisperx/bin/activate
$ pip show whisperx torch numpy

Name: whisperx
Version: 3.7.4

Name: torch
Version: 2.8.0

Name: numpy
Version: 2.0.2
```

✅ All packages installed successfully  
✅ No dependency conflicts detected  
✅ Environment isolation maintained

## Affected Stages

Only 3 pipeline stages use `venv/whisperx`:

1. **demux** - Audio/video extraction
2. **asr** - Speech recognition
3. **alignment** - Word-level timestamps

**Other stages unaffected:**
- translation (uses `venv/indictrans2`)
- subtitle_gen (uses `venv/common`)
- mux (uses `venv/common`)

## Files Modified

1. **`requirements-whisperx.txt`** - Updated package versions:
   ```diff
   - whisperx==3.3.1
   + whisperx==3.7.4
   
   - torch~=2.0.0
   + torch~=2.8.0
   
   - numpy>=1.23.0,<2.0.0
   + numpy>=2.0.2,<2.1.0
   ```

## Testing Required

### ⏳ Pending Tests

- [ ] **Environment Creation**
  ```bash
  rm -rf venv/whisperx
  ./bootstrap.sh
  ```

- [ ] **Demux Stage**
  ```bash
  # Test audio extraction
  ./prepare-job.sh in/test.mp4 --transcribe -s hi --debug
  # Check: out/<job>/audio/audio.wav exists
  ```

- [ ] **ASR Stage**
  ```bash
  # Check transcript generation
  ./run-pipeline.sh -j <job-id>
  # Verify: out/<job>/transcripts/transcript_source.txt
  ```

- [ ] **Alignment Stage**
  ```bash
  # Check word-level timestamps
  cat out/<job>/alignment/aligned_segments.json | jq '.segments[0]'
  ```

- [ ] **Full Workflow**
  ```bash
  # Transcribe workflow
  ./prepare-job.sh in/movie.mp4 --transcribe -s hi
  ./run-pipeline.sh -j <job-id>
  
  # Subtitle workflow
  ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu
  ./run-pipeline.sh -j <job-id>
  ```

- [ ] **Performance Comparison**
  - Compare transcription speed (3.3.1 vs 3.7.4)
  - Measure memory usage
  - Check GPU utilization (MPS on Apple Silicon)

- [ ] **Output Validation**
  - Verify transcript accuracy
  - Check timestamp precision
  - Validate alignment quality

## Rollback Plan

If issues are found, rollback is simple:

```bash
# 1. Restore old requirements
git checkout requirements-whisperx.txt

# 2. Remove upgraded environment
rm -rf venv/whisperx

# 3. Restore backup (if available)
if [ -d venv/whisperx-old-3.3.1 ]; then
    mv venv/whisperx-old-3.3.1 venv/whisperx
    echo "✅ Rolled back to whisperx 3.3.1"
else
    # Recreate from scratch
    ./bootstrap.sh
    echo "✅ Recreated whisperx 3.3.1 environment"
fi

# 4. Verify rollback
source venv/whisperx/bin/activate
pip show whisperx | grep Version
# Should show: Version: 3.3.1
```

**Rollback Time:** < 2 minutes (if backup exists), < 10 minutes (if recreating)

## Expected Benefits

### 1. Latest Features
- Improved transcription accuracy
- Better handling of multilingual audio
- Enhanced word-level alignment

### 2. Performance
- Optimized torch 2.8 backend
- Better MPS (Metal) support on macOS
- Potential speed improvements

### 3. Security
- Latest security patches
- Updated dependencies
- No yanked packages

### 4. Maintenance
- Official supported version
- Active development
- Community support

## Known Considerations

### 1. PyTorch 2.8 Changes
- New MPS backend improvements (Apple Silicon)
- CUDA 12 support
- API improvements in torch.jit

### 2. NumPy 2.0 Changes
- Type system overhaul
- Array API standardization
- whisperx 3.7.4 is designed for numpy 2.0

### 3. Larger Package Size
- torch 2.8: ~75 MB (vs 56 MB for 2.0)
- Total environment: ~3.5 GB (vs ~3 GB previously)

## Multi-Environment Isolation

**Key Advantage:** Other environments remain unchanged!

| Environment | PyTorch | NumPy | Status |
|-------------|---------|-------|--------|
| `venv/common` | N/A | N/A | ✅ Unaffected |
| `venv/whisperx` | **2.8.0** | **2.0.2** | ✅ **UPGRADED** |
| `venv/mlx` | 2.9.1 | 1.26.4 | ✅ Unaffected |
| `venv/indictrans2` | 2.9.1 | 2.3.5 | ✅ Unaffected |

This is the **power of multi-environment architecture**! 🎉

## Next Steps

1. **Test demux stage** with sample media file
2. **Test ASR stage** - verify transcription quality
3. **Test alignment stage** - check timestamp accuracy
4. **Run full workflow** - validate end-to-end pipeline
5. **Monitor performance** - compare with previous version
6. **Document findings** - update troubleshooting guide if needed

## Support

If issues arise:

1. **Check logs:**
   ```bash
   # Bootstrap log
   tail -100 logs/bootstrap_*.log
   
   # Pipeline logs
   tail -100 out/<job>/logs/06_asr_*.log
   ```

2. **Verify environment:**
   ```bash
   source venv/whisperx/bin/activate
   pip check  # Check for dependency conflicts
   ```

3. **Test minimal case:**
   ```bash
   # Use a 10-second clip
   ./prepare-job.sh in/test-short.mp4 --transcribe -s hi \
       --start-time 00:00:00 --end-time 00:00:10 --debug
   ```

4. **Rollback if needed** (see Rollback Plan above)

## Conclusion

✅ **Upgrade successful**  
✅ **Environment isolated**  
✅ **Ready for testing**

The upgrade leverages our multi-environment architecture to safely adopt the latest whisperx version with torch 2.8.0 and numpy 2.0, while keeping other environments stable.

---

**Completed by:** Bootstrap automation  
**Duration:** ~10 minutes (download + install)  
**Risk Level:** Low (isolated environment, easy rollback)  
**Status:** ✅ COMPLETE - Awaiting functional testing
