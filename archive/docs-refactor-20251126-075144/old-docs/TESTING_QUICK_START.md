# Quick Reference - Glossary System Testing

## Test the System

```bash
./test-glossary-quickstart.sh
```

Default video: `/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4`

## What Gets Tested

1. **Baseline Test** (no glossary) - Press 'y' when prompted
2. **Glossary Test** (with glossary) - Press 'y' when prompted  
3. **Cache Test** (verify caching) - Press 'y' when prompted

## Expected Results

### Baseline Test
- ✓ Pipeline runs WITHOUT glossary
- ✓ Message: "Glossary system is disabled (skipping)" ← This is CORRECT
- ✓ Subtitles generated without entity enhancement
- ✓ Time: ~15-20 minutes (5-min clip)

### Glossary Test
- ✓ Pipeline runs WITH glossary
- ✓ Message: "✓ Glossary system loaded successfully"
- ✓ TMDB cache MISS (first run)
- ✓ Subtitles with enhanced names
- ✓ Time: ~15-20 minutes (5-min clip)

### Cache Test
- ✓ Pipeline runs with same film
- ✓ TMDB cache HIT
- ✓ TMDB stage ~90% faster
- ✓ Same quality output
- ✓ Time: ~15-20 minutes (5-min clip)

## Stage Order (Correct)

```
01_demux
02_tmdb
03_glossary_load          ← Sequential!
04_source_separation
05_pyannote_vad
06_asr
07_alignment
08_lyrics_detection
09_export_transcript
10_translation            ← Sequential!
11_subtitle_generation    ← Sequential!
12_mux
```

## Troubleshooting

### "Could not find job directory"
- ✅ FIXED in Session 3
- Path extraction now uses: `grep "^Job directory:" | head -1 | xargs`

### "Glossary system is disabled"  
- ✅ This is EXPECTED for baseline tests
- Glossary test will have it enabled

### "Stage 02b_glossary_load"
- ✅ FIXED in Session 2
- Now properly numbered as 03_glossary_load

### Recursion Error
- ✅ Not present in current code
- If seen, check you're using latest version

## Results Location

```
test-results/
├── baseline/        # Baseline test outputs
├── glossary/        # Glossary test outputs
├── cache/           # Cache test outputs
└── quick-diff.txt   # Comparison results
```

## Documentation

- `docs/PHASE1_SESSION1_COMPLETE.md` - Cache infrastructure
- `docs/PHASE1_SESSION2_COMPLETE.md` - Glossary manager
- `docs/PHASE1_SESSION3_COMPLETE.md` - Bug fixes
- `docs/GLOSSARY_SYSTEM_OPTIMIZATION.md` - Full design

## Status

✅ **Phase 1: COMPLETE**  
✅ **All Issues: RESOLVED**  
✅ **System: READY FOR TESTING**

Ready to run when you are!
