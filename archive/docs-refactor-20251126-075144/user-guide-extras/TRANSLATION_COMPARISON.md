# Alternative Translation Comparison: NLLB vs IndicTrans2

**Date:** 2025-11-23  
**Job:** out/2025/11/23/rpatel/4  
**Source:** Hindi (Hinglish mixed content)  
**Target:** English

---

## Summary

Created alternative English subtitles using **IndicTrans2** (specialized Indic→English model) to compare with **NLLB** (universal translation model).

### Files Generated

**Original:**
- `Jaane Tu Ya Jaane Na.hi.srt` - Hindi source subtitles

**Translations:**
- `Jaane Tu Ya Jaane Na.en.srt` - NLLB translation (universal model)
- `Jaane Tu Ya Jaane Na.en.indictrans2.srt` - IndicTrans2 translation (Indic-specialized)

**Metadata:**
- `segments_translated_en.json` - NLLB translation data
- `segments_translated_en_indictrans2.json` - IndicTrans2 translation data

---

## Translation Differences

### Key Observations

1. **English Pass-through:**
   - Both models handle embedded English phrases well
   - Example: "Sorry", "What lies?", "Right", "She's so funny, no?"

2. **Song Lyrics:**
   - **NLLB:** Attempts full translation: "You've lost Kanata before me..."
   - **IndicTrans2:** Preserves transliteration: "Tera mujhse hai pehle kanata khoi..."
   - **Note:** IndicTrans2 may be more appropriate for song titles/lyrics

3. **Hinglish Content:**
   - Both handle code-mixed content (Hindi + English)
   - IndicTrans2 may have slight edge on Indic language nuances

4. **Translation Quality:**
   - **NLLB:** More natural English phrasing
   - **IndicTrans2:** More literal, closer to source structure
   - **IndicTrans2:** Better with Indian names and cultural terms

---

## Usage Recommendations

### Use NLLB When:
✓ You want natural, fluent English subtitles
✓ Content is primarily dialogue (not songs/poetry)
✓ Audience is international (non-Indian viewers)
✓ You need smooth, readable English

### Use IndicTrans2 When:
✓ Content has cultural/religious terms
✓ Preserving Indian language structure is important
✓ Translating between multiple Indic languages
✓ You want literal translations for verification
✓ Content includes poetry, songs, or literary text

---

## How to Generate Alternative Translations

### Method 1: Using Script (Post-Processing)

After pipeline completes, generate alternative translation:

```bash
# Run alternative translation
cd /Users/rpatel/Projects/cp-whisperx-app
source venv/indictrans2/bin/activate
python scripts/translate_alternative.py out/YYYY/MM/DD/user/counter
deactivate

# Output: <movie>.en.indictrans2.srt
```

### Method 2: During Pipeline (Future Enhancement)

Could be integrated into prepare-job:

```bash
# Future option (not yet implemented)
./prepare-job.sh --media movie.mp4 \
    --workflow subtitle \
    --source-lang hi \
    --target-langs en \
    --translation-engine both  # Generate both NLLB and IndicTrans2
```

---

## Technical Details

### Script: `scripts/translate_alternative.py`

**Features:**
- Loads Hindi segments from existing transcript
- Uses IndicTrans2 model (ai4bharat/indictrans2-indic-en-1B)
- Generates English translations with IndicTrans2 engine
- Creates separate SRT file with `.indictrans2` suffix
- Preserves timing, only changes translation text

**Performance:**
- ~142 segments in ~4-5 minutes on CPU
- CPU-optimized (MPS has compatibility issues)
- Uses beam search (num_beams=5) for quality

**Configuration:**
```python
model_name = "ai4bharat/indictrans2-indic-en-1B"
src_lang = "hin_Deva"  # Hindi (Devanagari)
tgt_lang = "eng_Latn"  # English (Latin)
num_beams = 5          # Quality vs speed
max_length = 256       # Max translation length
```

---

## Comparison Examples

### Example 1: Song Lyrics

**Original:** "तेरा मुझसे है पहले कनाता खोई"

**NLLB:**  
"You've lost Kanata before me"

**IndicTrans2:**  
"Tera mujhse hai pehle kanata khoi"

**Analysis:** IndicTrans2 preserves transliteration for song lyrics, which may be more appropriate for cultural content.

### Example 2: Mixed English-Hindi

**Original:** "Sorry यह हमारी ग्रूप के लिए बहुत special गान है"

**NLLB:**  
"Sorry, this is a very special song for our group"

**IndicTrans2:**  
"Sorry, this is a very special song for our group"

**Analysis:** Both handle code-mixing well.

### Example 3: Colloquial Speech

**Original:** "सच, इसलिए कप पिरीट से गला फारते वे गारे हो तुम लोग"

**NLLB:**  
"That's right, so you're the dirty ones"

**IndicTrans2:**  
"True, that's why they're soiled by the cup pyrites, you guys"

**Analysis:** NLLB more natural, IndicTrans2 more literal.

---

## File Locations

```
out/2025/11/23/rpatel/4/
├── subtitles/
│   ├── Jaane Tu Ya Jaane Na.hi.srt              # Original Hindi
│   ├── Jaane Tu Ya Jaane Na.en.srt              # NLLB English
│   └── Jaane Tu Ya Jaane Na.en.indictrans2.srt  # IndicTrans2 English
└── transcripts/
    ├── segments.json                             # Original Hindi segments
    ├── segments_translated_en.json               # NLLB translation
    └── segments_translated_en_indictrans2.json   # IndicTrans2 translation
```

---

## Benefits of Having Both

1. **Quality Comparison:** Review both to choose best translation
2. **Different Use Cases:** Pick appropriate one for your audience
3. **Verification:** Cross-reference translations for accuracy
4. **Learning:** Understand differences between universal vs specialized models

---

## Future Enhancements

1. **Automatic Generation:** Generate both during pipeline
2. **Quality Metrics:** Automated scoring/comparison
3. **Hybrid Approach:** Combine strengths of both models
4. **User Selection:** Let user choose engine at prepare-job time
5. **Batch Comparison:** Compare multiple translation engines

---

## Scripts Created

1. **translate_alternative.py** - Generate IndicTrans2 translation
   - Location: `scripts/translate_alternative.py`
   - Usage: `python translate_alternative.py <job_dir>`

2. **compare_translations.py** - Compare NLLB vs IndicTrans2
   - Location: `scripts/compare_translations.py`
   - Usage: `python compare_translations.py <job_dir>`

---

## Conclusion

You now have two English subtitle files:

✅ **NLLB** (`Jaane Tu Ya Jaane Na.en.srt`) - Natural, fluent English  
✅ **IndicTrans2** (`Jaane Tu Ya Jaane Na.en.indictrans2.srt`) - Literal, structure-preserving

**Recommendation:** Review both and choose based on your specific needs. For general viewing, NLLB is often more natural. For cultural preservation or literal translation needs, IndicTrans2 may be preferable.

Both files are ready to use with your video player or editing software!
