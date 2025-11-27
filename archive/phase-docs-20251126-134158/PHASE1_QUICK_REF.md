# Phase 1 Quick Reference Card

## Status: ✅ COMPLETE - Ready for Test Run

### Test Command
```bash
./run-pipeline.sh -j job-20251126-rpatel-0001
```

### Monitor Progress
```bash
# Watch pipeline log
tail -f out/2025/11/26/rpatel/1/logs/pipeline.log

# Check stage progress
ls -lh out/2025/11/26/rpatel/1/*/
```

### View Results
```bash
# Transcripts
cat out/2025/11/26/rpatel/1/transcripts/*.txt

# Subtitles
ls -lh out/2025/11/26/rpatel/1/subtitles/

# ASR output
ls -lh out/2025/11/26/rpatel/1/06_asr/
```

## Configuration Applied

### Hardware
- Device: MPS (Apple Silicon GPU)
- Backend: MLX
- Compute: float16

### Bias Strategy
- Strategy: hybrid
- Window: 30s
- Stride: 10s
- TopK: 15

### Whisper
- Model: large-v3
- Temperature: 0.0,0.1,0.2
- Beam: 8
- Best Of: 8

## Expected Results

- **Accuracy**: 85-90%
- **Speed**: 30-40s for 5-min clip
- **Character Names**: 80-85% correct

## Success Criteria

✅ Pipeline completes without errors
✅ ASR stage produces transcript
✅ Character names recognized
✅ Processing time < 60s

## Next Phase

If successful → Phase 2 (Two-step transcription)
