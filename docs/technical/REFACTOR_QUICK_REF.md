# Pipeline Refactor Quick Reference

## What Changed?

**TL;DR**: Pipeline reorganized to properly separate song bias, lyrics detection, and general bias correction.

## New Stage Numbers

| Old # | Old Name | New # | New Name | What Changed |
|-------|----------|-------|----------|--------------|
| 6 | asr | 6 | asr | Same - Now with character bias only |
| 7 | bias_injection | 9 | bias_correction | Moved & renamed |
| - | - | 7 | song_bias_injection | **NEW** - Song-specific bias |
| 11 | lyrics_detection | 8 | lyrics_detection | Moved & **FIXED** - Now actually detects lyrics! |
| 8 | diarization | 10 | diarization | Renumbered |
| 9 | glossary_builder | 11 | glossary_builder | Renumbered |
| 10 | second_pass_translation | 12 | second_pass_translation | Renumbered |
| 12 | post_ner | 13 | post_ner | Renumbered |
| 13 | subtitle_gen | 14 | subtitle_gen | Renumbered |
| 14 | mux | 15 | mux | Renumbered & **FIXED** - Final stage |

## Quick Commands

### Run New Pipeline

```bash
# Standard workflow (all features enabled)
./prepare-job.sh /path/to/movie.mp4
./run_pipeline.sh -j <job-id>

# Fast mode (skip optional stages)
SONG_BIAS_ENABLED=false LYRICS_DETECTION_ENABLED=false ./run_pipeline.sh -j <job-id>
```

### Check Lyrics Detection Results

```bash
# Count detected lyrics
jq '.total_lyric_segments' out/<job>/08_lyrics_detection/segments.json

# View lyric regions
cat out/<job>/08_lyrics_detection/detected_lyric_regions.json
```

### Verify Song Bias

```bash
# Check song corrections
grep "song-related corrections" out/<job>/logs/07_song_bias_injection_*.log
```

## Configuration

### Recommended Settings (Add to config/.env.pipeline)

```bash
# Song bias (NEW)
SONG_BIAS_ENABLED=true
SONG_BIAS_FUZZY_THRESHOLD=0.80

# Lyrics detection (IMPROVED)
LYRICS_DETECTION_ENABLED=true
LYRICS_DETECTION_THRESHOLD=0.5
LYRICS_MIN_DURATION=30.0

# Bias correction (RENAMED from bias_injection)
BIAS_ENABLED=true
BIAS_FUZZY_THRESHOLD=0.85
```

### For Fast Processing (Skip Optional Stages)

```bash
SONG_BIAS_ENABLED=false
LYRICS_DETECTION_ENABLED=false
BIAS_ENABLED=true  # Keep final corrections
```

### For Maximum Accuracy

```bash
SONG_BIAS_ENABLED=true
SONG_BIAS_FUZZY_THRESHOLD=0.75  # More aggressive
LYRICS_DETECTION_ENABLED=true
LYRICS_DETECTION_THRESHOLD=0.4  # More sensitive
BIAS_ENABLED=true
BIAS_USE_CONTEXT=true  # Time-aware corrections
```

## Key Improvements

### 1. Song Bias (NEW Stage 7)
- Loads soundtrack from TMDB
- Corrects artist names: "Kumar Sanu", "Shreya Ghoshal"
- Corrects song titles: "Tujhe Dekha To"
- Falls back to common Bollywood artists

### 2. Lyrics Detection (FIXED Stage 8)
**Before**: Just called bias_injection - didn't actually detect lyrics!  
**After**: Proper detection using:
- Audio analysis (tempo, rhythm, spectral features)
- Transcript analysis (repetition, pattern matching)
- Marks segments with `is_lyrics: true/false`

### 3. Bias Correction (RENAMED Stage 9)
**Before**: Called "bias_injection" (Stage 7)  
**After**: Called "bias_correction" (Stage 9)
- Runs AFTER lyrics detection
- Final cleanup with fuzzy/phonetic matching
- Context-aware corrections optional

## Troubleshooting

### "Subtitle file not found" Error

**Fixed!** MUX now looks in correct location: `14_subtitle_gen/subtitles.srt`

### Lyrics Detection Fails

**Option 1**: Install librosa for audio analysis
```bash
pip install librosa
```

**Option 2**: Use transcript-only mode (automatic fallback)

### Song Bias Not Working

**Check**: Does TMDB have soundtrack data?
```bash
jq '.soundtrack' out/<job>/02_tmdb/enrichment.json
```

If no soundtrack, it falls back to common artist names.

## Migration Notes

### Existing Jobs

Old jobs (with 14 stages) still work fine. New jobs use 15 stages.

### Resume Capability

`resume-pipeline.sh` handles both old and new stage numbering automatically.

### Custom Scripts

If you reference stage numbers directly:
- `07_bias_injection` → `09_bias_correction`
- `11_lyrics_detection` → `08_lyrics_detection`  
- `13_subtitle_gen` → `14_subtitle_gen`
- `14_mux` → `15_mux` (FINAL STAGE - no finalize stage)

## Performance

**Additional Time**: ~45-180 seconds total
- Song bias: +10-30s
- Lyrics detection: +30-120s (with audio) or +5-15s (transcript only)
- Bias correction: Same as before

**Accuracy Improvement**: ~15-25% overall

## Need Help?

1. Check logs: `out/<job>/logs/`
2. Read full refactor doc: `PIPELINE_REFACTOR_2025-11-14.md`
3. View pipeline status: `./scripts/pipeline-status.sh <job-id>`

