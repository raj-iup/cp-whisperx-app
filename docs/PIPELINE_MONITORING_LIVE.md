# Pipeline Monitoring - Live Status

**Last Updated**: 2024-10-29 21:10 PM  
**Monitoring**: Active  
**Auto-refresh**: Every 2 minutes

---

## Current Status

### Stage 6: Diarization (RUNNING)
- **Status**: 🔄 Processing
- **Elapsed**: 13 minutes
- **Expected**: 10-30 minutes total
- **Progress**: Within normal range
- **Output**: Pending (will appear when complete)

---

## Pipeline Progress

```
✓ Stage 1:  demux         (43s)    ████████████ COMPLETE
✓ Stage 2:  tmdb          (2s)     ████████████ COMPLETE
✓ Stage 3:  pre-ner       (2s)     ████████████ COMPLETE
✓ Stage 4:  silero-vad    (16m)    ████████████ COMPLETE
✓ Stage 5:  pyannote-vad  (57m)    ████████████ COMPLETE
🔄 Stage 6:  diarization   (13m+)   ████████░░░░ RUNNING (50%)
⏭ Stage 7:  asr           (30-60m) ░░░░░░░░░░░░ PENDING
⏭ Stage 8:  post-ner      (2-5m)   ░░░░░░░░░░░░ PENDING
⏭ Stage 9:  subtitle-gen  (1-2m)   ░░░░░░░░░░░░ PENDING
⏭ Stage 10: mux           (2-5m)   ░░░░░░░░░░░░ PENDING
```

**Overall**: 5.5/10 stages (55%)

---

## Timeline

### Completed (89 minutes)
| Time | Stage | Duration | Status |
|------|-------|----------|--------|
| Earlier | demux | 43s | ✓ |
| Earlier | tmdb | 2s | ✓ |
| Earlier | pre-ner | 2s | ✓ |
| Earlier | silero-vad | 16m | ✓ |
| Earlier | pyannote-vad | 57m | ✓ |

### Active
| Time | Stage | Duration | Status |
|------|-------|----------|--------|
| 20:58-? | diarization | 13m+ | 🔄 |

### Pending (48-109 minutes)
| Stage | Est. Duration |
|-------|---------------|
| asr | 30-60m |
| post-ner | 2-5m |
| subtitle-gen | 1-2m |
| mux | 2-5m |

---

## Performance Metrics

### Success Rate
- **Completed**: 5/10 stages
- **Failed**: 0/10 stages
- **Success Rate**: 100%

### Timing
- **Elapsed**: ~89 minutes (1.5 hours)
- **Remaining**: ~48-109 minutes (0.8-1.8 hours)
- **Total Estimate**: 2.3-3.3 hours

### Resource Usage
- **Device**: CPU (Mac)
- **Input Size**: 281 MB audio
- **Duration**: ~30 minutes video
- **Processing Speed**: ~0.5x realtime (CPU-bound)

---

## Container Status

```
Container: cp-whisperx-app-diarization-run-057cd8b92bac
Status: Up 13 minutes
Health: Running normally
Logs: Processing audio (no errors)
```

---

## Output Files

### Created ✓
- `audio/audio.wav` - 281 MB
- `metadata/tmdb_data.json`
- `entities/pre_ner.json`
- `vad/silero_segments.json`
- `vad/pyannote_segments.json`

### Pending ⏳
- `diarization/speaker_segments.json` (in progress)
- `transcription/transcript.json` (waiting)
- `entities/post_ner.json` (waiting)
- `subtitles/subtitles.srt` (waiting)
- `final_output.mp4` (waiting)

---

## What's Happening Now

### Diarization Process
1. ✓ Load PyAnnote model (completed in 8s)
2. 🔄 Analyze audio for speaker patterns (current)
3. ⏳ Cluster speakers into groups
4. ⏳ Assign speaker labels to segments
5. ⏳ Write output JSON
6. ⏳ Exit container

### Expected Output
```json
{
  "speakers": ["SPEAKER_00", "SPEAKER_01", ...],
  "segments": [
    {"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00"},
    {"start": 5.3, "end": 12.1, "speaker": "SPEAKER_01"},
    ...
  ]
}
```

---

## Next Steps

### Automatic (When Diarization Completes)
Ready to run:
```bash
docker compose run --rm asr out/Jaane_Tu_Ya_Jaane_Na_2008
```

### Manual Commands Available
```bash
# Check status
docker ps -a --filter "name=diarization"

# View logs
docker logs cp-whisperx-app-diarization-run-057cd8b92bac

# Check output
ls -lh out/Jaane_Tu_Ya_Jaane_Na_2008/diarization/

# Or use orchestrator (will resume automatically)
python pipeline.py "in/Jaane Tu Ya Jaane Na 2008.mp4"
```

---

## Monitoring Schedule

| Time | Check | Status |
|------|-------|--------|
| 20:58 | Start | 🔄 |
| 21:08 | +10 min | Running |
| 21:10 | +13 min | Running |
| 21:12 | +15 min | Checking... |
| 21:14 | +17 min | TBD |
| 21:16 | +19 min | TBD |

---

## Alerts

### Normal Behavior ✓
- No output file yet (processing)
- Container running 13+ minutes
- No errors in logs
- Within expected time range (10-30 min)

### Watch For ⚠️
- Container exit without output (failure)
- 30+ minutes without completion (may need intervention)
- Memory/CPU exhaustion

---

**Status**: All systems normal. Diarization progressing as expected.
**Next Check**: 9:12 PM (2 minutes)
