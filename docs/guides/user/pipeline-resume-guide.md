# Pipeline Resume & Recovery Guide

## Quick Reference

### Resume Failed Job
```bash
# Automatically resume from where it stopped
python pipeline.py --job 20251102-0004
```

### Check Job Status
```bash
# View manifest to see progress
cat out/2025/11/02/20251102-0004/manifest.json | jq .pipeline

# Check latest logs
ls -lt out/2025/11/02/20251102-0004/logs/
```

### Run Specific Stages
```bash
# Run only ASR stage
python pipeline.py --job 20251102-0004 --stages asr

# Run ASR and subsequent stages
python pipeline.py --job 20251102-0004 --stages asr post_ner subtitle_gen mux
```

### Start Fresh
```bash
# Ignore previous progress and restart from beginning
python pipeline.py --job 20251102-0004 --no-resume
```

## Pipeline Architecture

### Stage Sequence (10 stages)
1. **demux** (600s) - Extract audio from video
2. **tmdb** (120s) - Fetch movie metadata
3. **pre_ner** (300s) - Extract named entities for ASR hints
4. **silero_vad** (1800s) - Voice activity detection
5. **pyannote_vad** (3600s) - Refined VAD
6. **diarization** (7200s) - Speaker identification
7. **asr** (14400s) - Transcription + Translation + Alignment ⚠️
8. **post_ner** (1200s) - Post-processing named entities
9. **subtitle_gen** (600s) - Generate subtitle files
10. **mux** (600s) - Merge subtitles with video

⚠️ ASR is the longest stage - ~4 hours for 2.5 hour movie on CPU

## Manifest Tracking

The pipeline uses `manifest.json` to track state:

```json
{
  "pipeline": {
    "status": "failed|completed|running",
    "completed_stages": ["demux", "tmdb", ...],
    "failed_stages": ["asr"]
  },
  "stages": {
    "asr": {
      "completed": true,
      "status": "failed",
      "duration": 2235.85,
      "error": "Container execution failed"
    }
  }
}
```

## Resume Logic

When you run with resume enabled (default):

1. **Load manifest.json** from output directory
2. **Check completed_stages** array
3. **Skip completed stages** automatically
4. **Resume at first incomplete** stage

Example for job 20251102-0004:
- Stages 1-6 completed ✅
- Stage 7 (ASR) failed ❌
- Resume will **skip 1-6**, start at **7**

## Improvements Made (Nov 2, 2025)

### 1. Smart Error Filtering
- Ignores progress bars in stderr (%, █, MB/s)
- Only logs actual errors (error, exception, failed)

### 2. Increased ASR Timeout
- Before: 3 hours (10800s)
- After: 4 hours (14400s)

### 3. Retry Logic
- ASR stage: 2 retries (3 total attempts)
- Other stages: 1 attempt

### 4. Better Error Handling
- Proper exit code checking
- Partial output on timeout
- Clearer error messages

## Performance Tips

### Use GPU if Available
Edit job config: `jobs/YYYY/MM/DD/JOBID/.JOBID.env`

```bash
# For GPU
device_whisperx=cuda
whisper_compute_type=float16
whisper_batch_size=16

# For CPU (current)
device_whisperx=cpu
whisper_compute_type=int8
whisper_batch_size=8
```

### Monitor Progress
```bash
# Watch latest ASR log
tail -f out/2025/11/02/20251102-0004/logs/07_asr_*.log

# Watch orchestrator log
tail -f out/2025/11/02/20251102-0004/logs/00_orchestrator_*.log
```

## Troubleshooting

### Job Not Found
```bash
✗ Error: Job not found: 20251102-0004

# Solution: Check job exists
ls jobs/2025/11/02/
cat jobs/2025/11/02/jobs.json
```

### Stage Keeps Failing
```bash
# Check stage-specific log
cat out/YYYY/MM/DD/JOBID/logs/07_asr_*.log

# Try running just that stage
python pipeline.py --job JOBID --stages asr

# Check Docker status
docker ps
docker logs cp_whisperx_asr
```

### Memory Issues
```bash
# Reduce batch size in job config
whisper_batch_size=4  # Lower = less memory

# Check system resources
docker stats
```

## List Available Stages
```bash
python pipeline.py --list-stages
```

Output:
```
Available pipeline stages:
 1. demux           → demux           (timeout:  600s) [CRITICAL]
 2. tmdb            → tmdb            (timeout:  120s) [optional]
 3. pre_ner         → pre-ner         (timeout:  300s) [optional]
 4. silero_vad      → silero-vad      (timeout: 1800s) [CRITICAL]
 5. pyannote_vad    → pyannote-vad    (timeout: 3600s) [CRITICAL]
 6. diarization     → diarization     (timeout: 7200s) [CRITICAL]
 7. asr             → asr             (timeout: 14400s) [CRITICAL]
 8. post_ner        → post-ner        (timeout: 1200s) [optional]
 9. subtitle_gen    → subtitle-gen    (timeout:  600s) [CRITICAL]
10. mux             → mux             (timeout:  600s) [CRITICAL]
```

## Summary

✅ **Resume works automatically** - Just rerun the same command
✅ **Tracks all stage completions** - Via manifest.json
✅ **Skip completed stages** - No wasted computation
✅ **Retry on failure** - ASR has 2 retries built in
✅ **Flexible execution** - Run any stage(s) individually

The pipeline orchestrator is robust and production-ready for long-running jobs with automatic recovery.
