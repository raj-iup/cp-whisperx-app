# Test 3: Subtitle Workflow - Partially Complete ⚠️

**Date:** 2025-12-05 (21:35-21:45 UTC)  
**Job ID:** job-20251205-rpatel-0016  
**Job Directory:** `out/2025/12/05/rpatel/16/`

## Summary

Subtitle workflow completed with 2 out of 5 target languages successfully embedded in video. All 5 translations completed successfully, but only 2 subtitle tracks were muxed into the final video.

## Configuration

- **Source Media:** `in/test_clips/jaane_tu_test_clip.mp4` (Hinglish/Bollywood)
- **Source Language:** Hindi (hi)
- **Target Languages:** en, gu, ta, es, ru (5 languages)
- **Workflow:** Subtitle (multi-language soft-embedded subtitles)
- **Duration:** ~2.5 minutes audio

## Pipeline Execution

### Stage Timings:
1. **Demux:** 0.8s (audio extraction)
2. **TMDB:** 0.3s (failed, continued without metadata) ⚠️
3. **Glossary:** 0.0s (disabled)
4. **Source Separation:** 84.3s (~1.4 min)
5. **PyAnnote VAD:** 20.5s (19 speech segments detected)
6. **ASR (MLX):** 69.7s (~1.2 min) - 84 segments transcribed
7. **Alignment:** FAILED initially, then SKIPPED ⚠️
8. **Translation (5 languages):** ~100s total
   - English: 15.4s (IndicTrans2)
   - Gujarati: ~20s (IndicTrans2)
   - Tamil: ~20s (IndicTrans2)
   - Spanish: ~22s (NLLB)
   - Russian: 22.5s (NLLB)
9. **Subtitle Generation:** ~0.1s (6 files: hi + 5 targets)
10. **Hinglish Detection:** FAILED (script missing) ⚠️
11. **Mux:** 0.2s (only 2 tracks embedded) ⚠️

**Total Time:** ~5 minutes

### Issues Fixed During Run:
1. ✅ **TMDB error handling** - Syntax error in exc_info parameter
2. ✅ **Alignment warnings suppression** - WhisperX logs interfering with JSON output
3. ✅ **Translation filename standardization** - segments_{lang}.json → segments_translated_{lang}.json
4. ✅ **Subtitle generation logging** - Added directory creation and better error logging

### Issues Encountered:
1. ⚠️ **Alignment stage failed** - WhisperX warnings polluting stdout (partially fixed)
2. ⚠️ **TMDB stage failed** - Script error (non-blocking, continued)
3. ⚠️ **Hinglish detection failed** - Script not found (non-blocking)
4. ⚠️ **Incomplete muxing** - Only 2/5 subtitle tracks embedded

## Output Files

### Translation Directory: `10_translation/`

**All 5 languages translated successfully:**
1. ✅ **segments_translated_en.json** - 37 KB (IndicTrans2)
2. ✅ **segments_translated_gu.json** - 37 KB (IndicTrans2)
3. ✅ **segments_translated_ta.json** - 37 KB (IndicTrans2)
4. ✅ **segments_translated_es.json** - 37 KB (NLLB)
5. ✅ **segments_translated_ru.json** - 38 KB (NLLB)

### Subtitle Directory: `subtitles/`

**All 6 subtitle files generated successfully:**
1. ✅ **jaane tu test clip.hi.srt** - 5.1 KB (source Hindi)
2. ✅ **jaane tu test clip.en.srt** - 5.1 KB (English)
3. ✅ **jaane tu test clip.gu.srt** - 5.1 KB (Gujarati)
4. ✅ **jaane tu test clip.ta.srt** - 5.1 KB (Tamil)
5. ✅ **jaane tu test clip.es.srt** - 5.2 KB (Spanish)
6. ✅ **jaane tu test clip.ru.srt** - 6.6 KB (Russian - Cyrillic)

### Muxed Video: `10_mux/`

**Video with embedded subtitles:**
- ⚠️ **jaane tu test clip_subtitled.mp4** - 27.7 MB
  - ✅ Track 1: English (eng) - mov_text codec
  - ✅ Track 2: Hindi (hin) - mov_text codec
  - ❌ Track 3: Gujarati - NOT EMBEDDED
  - ❌ Track 4: Tamil - NOT EMBEDDED
  - ❌ Track 5: Spanish - NOT EMBEDDED
  - ❌ Track 6: Russian - NOT EMBEDDED

## Sample Output

### Hindi Subtitle (Source):
```srt
1
00:00:00,000 --> 00:00:02,020
मेरे बहुत सारे दोस्त वापस आ रहे हैं और तुम्हें पता है...

2
00:00:02,020 --> 00:00:04,100
मैं भी बहुत ज्यादा वापस आ रहा हूं
```

### English Subtitle (IndicTrans2):
```srt
1
00:00:00,000 --> 00:00:02,020
I have a lot of friends who are returning and you know...

2
00:00:02,020 --> 00:00:04,100
I'm also coming back a lot
```

### Russian Subtitle (NLLB):
```srt
1
00:00:00,000 --> 00:00:02,020
У меня много друзей, которые возвращаются, и ты знаешь...

2
00:00:02,020 --> 00:00:04,100
Я тоже возвращаюсь много
```

## Verification

### Completed Successfully:
✅ Demux (audio extraction)  
✅ Source separation (vocals extracted)  
✅ PyAnnote VAD (19 speech segments)  
✅ ASR (84 segments transcribed)  
✅ Translation (5 languages, all completed)  
✅ Subtitle generation (6 SRT files created)  
✅ Partial mux (2 tracks embedded)

### Issues Requiring Follow-up:
⚠️ Alignment stage - Needs better stdout/stderr separation  
⚠️ TMDB enrichment - Script error needs investigation  
⚠️ Hinglish detection - Script missing  
⚠️ Mux stage - Only embedded 2/6 subtitle tracks  
⚠️ Mux directory - Files in 10_mux instead of 12_mux (stage numbering mismatch)

## Quality Assessment

### Translation Quality:
- **IndicTrans2 (Hindi→English):** Natural phrasing, good accuracy
- **IndicTrans2 (Hindi→Gujarati):** Good accuracy expected (both Indic)
- **IndicTrans2 (Hindi→Tamil):** Good accuracy expected (both Indic)
- **NLLB (Hindi→Spanish):** Adequate translation
- **NLLB (Hindi→Russian):** Cyrillic script properly rendered

### Subtitle Quality:
- Timing preserved from ASR segments
- All subtitle files properly formatted (SRT)
- Russian subtitles use Cyrillic script (6.6 KB vs ~5 KB for others)

## Next Steps

1. **Fix mux stage logic** - Embed all 5 target language subtitle tracks
2. **Investigate alignment warnings** - Further suppress WhisperX library logs
3. **Fix TMDB script** - Debug and repair TMDB enrichment stage
4. **Add hinglish_word_detector.py** - Create missing script or disable feature
5. **Fix stage directory numbering** - Mux output should be in 12_mux not 10_mux

## Files

- **Log:** `test3-subtitle-workflow.log`
- **Output Video:** `out/2025/12/05/rpatel/16/10_mux/jaane tu test clip_subtitled.mp4`
- **Subtitles:** `out/2025/12/05/rpatel/16/subtitles/*.srt` (6 files)
- **Translations:** `out/2025/12/05/rpatel/16/10_translation/segments_translated_*.json` (5 files)

---

**Status:** ⚠️ Partially Complete  
**Success Rate:** 75% (6/8 stages fully successful)  
**Critical Issue:** Mux stage only embedded 2/5 subtitle tracks  
**Performance:** Good - ~5 min total for multi-language subtitle generation
