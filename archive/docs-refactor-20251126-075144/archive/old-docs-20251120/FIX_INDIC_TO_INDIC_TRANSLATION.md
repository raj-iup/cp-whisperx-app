# Fix: Indic-to-Indic Translation Support

**Date:** 2024-11-20  
**Issue:** IndicTrans2 doesn't support direct Indic→Indic translation (e.g., hi→gu)

## Problem

### Error from Log

```
[WARNING] IndicTrans2 does not support hi→gu. Supported: Any Indic language → English/non-Indic
```

### User Request

```bash
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu
```

**Expected:** Hindi audio transcribed, then translated to **English** and **Gujarati**

**Actual Result:**
- ✅ English translation works (hi→en)
- ❌ Gujarati subtitles show Hindi text (translation didn't happen)

### Root Cause

**IndicTrans2 model limitations:**

| Model | Direction | Supported |
|-------|-----------|-----------|
| `indictrans2-indic-en-1B` | Indic → English | ✅ Yes |
| `indictrans2-indic-en-1B` | Indic → Indic | ❌ No |
| `indictrans2-en-indic-1B` | English → Indic | ✅ Yes (different model) |

**Problem:** User requested **hi→gu** but IndicTrans2 only supports:
- hi→en (with indictrans2-indic-en model)
- en→gu (with indictrans2-en-indic model - not loaded)

## Architecture Understanding

### IndicTrans2 Models

AI4Bharat provides **two separate models**:

1. **`ai4bharat/indictrans2-indic-en-1B`**
   - Direction: Indic → English
   - Size: 1B parameters
   - Languages: 22 Indic languages → English
   - Example: hi→en, ta→en, bn→en

2. **`ai4bharat/indictrans2-en-indic-1B`**
   - Direction: English → Indic
   - Size: 1B parameters
   - Languages: English → 22 Indic languages
   - Example: en→hi, en→ta, en→bn

### Translation Paths

**Supported (single-step):**
```
Hindi → English    (indictrans2-indic-en model)
Tamil → English    (indictrans2-indic-en model)
```

**NOT Supported (direct):**
```
Hindi → Gujarati   ❌ No direct model
Tamil → Telugu     ❌ No direct model
```

**Solution: Two-step pivot through English:**
```
Hindi → English → Gujarati
  ↓         ↓         ↓
Step 1    Step 2    Result
(model 1) (model 2)
```

## Solution Options

### Option 1: Two-Step Translation (Current Implementation)

**Process:**
1. Load source transcript (Hindi)
2. Translate hi→en using `indictrans2-indic-en` model
3. Translate en→gu using `indictrans2-en-indic` model
4. Generate subtitles from final translation

**Pros:**
- High quality (uses official models)
- Maintains meaning through English pivot
- Leverages existing infrastructure

**Cons:**
- Requires loading two large models (~2GB each)
- 2x translation time
- Requires `indictrans2-en-indic` model (not currently installed)

### Option 2: Fallback to Source (Temporary Solution)

**Process:**
1. Detect unsupported language pair (hi→gu)
2. Log warning
3. Return source text unchanged
4. Generate subtitles with source text

**Current behavior - user gets:**
- ✅ Hindi subtitles (source)
- ✅ English subtitles (translated)
- ⚠️ "Gujarati" subtitles with Hindi text

**Pros:**
- Simple
- No additional models needed
- Users still get content (in source language)

**Cons:**
- Not actual translation
- User requested Gujarati but gets Hindi

### Option 3: Skip Unsupported Pairs

**Process:**
1. Detect unsupported language pair
2. Don't generate that subtitle track
3. Only generate supported translations

**Result for `-t en,gu`:**
- ✅ English subtitles generated
- ⚠️ Gujarati subtitles skipped (with warning message)

**Pros:**
- Clear and honest
- No misleading content

**Cons:**
- User doesn't get requested language

## Implementation

### Current Fix (Partial - Option 2)

Updated `scripts/indictrans2_translator.py`:

```python
def translate_whisperx_result(
    source_result: Dict[str, Any],
    source_lang: str = "hi",
    target_lang: str = "en",
    logger = None
) -> Dict[str, Any]:
    """
    Translate WhisperX result using IndicTrans2.
    
    Supports:
    - Indic → English (direct, single-step)
    - Indic → Indic (placeholder - returns source for now)
    - Indic → non-Indic (direct, single-step)
    """
    # Case 1: Direct Indic→English/non-Indic (supported)
    if can_use_indictrans2(source_lang, target_lang):
        # Translate normally
        pass
    
    # Case 2: Indic→Indic (not directly supported)
    elif is_indic_language(source_lang) and is_indic_language(target_lang):
        if logger:
            logger.warning(
                f"IndicTrans2 requires two-step translation for {source_lang}→{target_lang}: "
                f"{source_lang}→en→{target_lang}"
            )
            logger.warning(
                f"English→{target_lang} translation requires indictrans2-en-indic model. "
                f"Currently only indictrans2-indic-en model is loaded. "
                f"Returning source text unchanged."
            )
        
        # For now: return source unchanged
        return source_result
    
    # Case 3: Unsupported language pair
    else:
        if logger:
            logger.warning(f"Unsupported: {source_lang}→{target_lang}")
        return source_result
```

### Future Enhancement: Full Two-Step Translation

To fully implement Option 1, we need to:

1. **Add second model to bootstrap:**

```bash
# scripts/bootstrap.sh
# In venv/indictrans2 setup:
pip install huggingface-hub transformers torch
huggingface-cli login  # Get access to both models

# Pre-download both models
python -c "
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# Model 1: Indic→English
AutoTokenizer.from_pretrained('ai4bharat/indictrans2-indic-en-1B')
AutoModelForSeq2SeqLM.from_pretrained('ai4bharat/indictrans2-indic-en-1B')
# Model 2: English→Indic
AutoTokenizer.from_pretrained('ai4bharat/indictrans2-en-indic-1B')
AutoModelForSeq2SeqLM.from_pretrained('ai4bharat/indictrans2-en-indic-1B')
"
```

2. **Enhanced translator class:**

```python
class DualDirectionTranslator:
    """Handles both Indic→EN and EN→Indic translation"""
    
    def __init__(self):
        self.indic_to_en = None  # indictrans2-indic-en-1B
        self.en_to_indic = None  # indictrans2-en-indic-1B
    
    def translate_with_pivot(self, text, src_lang, tgt_lang):
        """
        Two-step translation: src_lang → en → tgt_lang
        """
        # Step 1: Load indic→en model
        if self.indic_to_en is None:
            self.indic_to_en = load_model("indictrans2-indic-en-1B")
        
        # Translate to English
        english_text = self.indic_to_en.translate(text, src_lang, "en")
        
        # Step 2: Load en→indic model
        if self.en_to_indic is None:
            self.en_to_indic = load_model("indictrans2-en-indic-1B")
        
        # Translate to target Indic language
        final_text = self.en_to_indic.translate(english_text, "en", tgt_lang)
        
        return final_text
```

3. **Update config for both models:**

```bash
# config/.env.pipeline
INDICTRANS2_MODEL_INDIC_EN=ai4bharat/indictrans2-indic-en-1B
INDICTRANS2_MODEL_EN_INDIC=ai4bharat/indictrans2-en-indic-1B
```

## User Experience

### Before Fix

```bash
$ ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu
```

**Output:**
```
✓ English subtitles: "Band? Why?"
✗ Gujarati subtitles: "बैंड? क्यों?" (still Hindi!)
```

### After Fix (Current - Fallback)

```bash
$ ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu
```

**Output with clear logging:**
```
[INFO] Translating hi→en... ✓
[WARNING] Indic→Indic translation (hi→gu) requires two models:
  • indictrans2-indic-en-1B (loaded)
  • indictrans2-en-indic-1B (not loaded)
[WARNING] Returning source text for gu subtitles
[INFO] Generated subtitles:
  • en: Translated to English ✓
  • gu: Source language (Hindi) - translation pending model installation
```

### After Full Implementation (Future)

```bash
$ ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu
```

**Output:**
```
[INFO] Translating hi→en... ✓
[INFO] Two-step translation hi→gu:
  • Step 1/2: hi→en... ✓
  • Step 2/2: en→gu... ✓
[INFO] Generated subtitles:
  • en: "Band? Why?" ✓
  • gu: "બેન્ડ? શા માટે?" ✓ (actual Gujarati!)
```

## Configuration

### Language Support Matrix

| Source | Target | Method | Models Required | Status |
|--------|--------|--------|-----------------|--------|
| hi | en | Direct | indictrans2-indic-en | ✅ Works |
| ta | en | Direct | indictrans2-indic-en | ✅ Works |
| hi | gu | Pivot | indic-en + en-indic | ⚠️ Partial |
| ta | te | Pivot | indic-en + en-indic | ⚠️ Partial |
| en | hi | Direct | indictrans2-en-indic | ❌ Not installed |
| en | ta | Direct | indictrans2-en-indic | ❌ Not installed |

**Legend:**
- ✅ Works: Fully functional
- ⚠️ Partial: Returns source text (fallback)
- ❌ Not installed: Model not available

### Installation Requirements

**Current setup (venv/indictrans2):**
```bash
$ pip list | grep -i indic
# indictrans2-indic-en model downloaded
```

**Full setup (for Indic→Indic):**
```bash
$ pip install huggingface-hub transformers torch IndicTransToolkit
$ huggingface-cli login  # Authenticate
$ python -c "
from transformers import AutoModelForSeq2SeqLM
# Download both direction models
AutoModelForSeq2SeqLM.from_pretrained('ai4bharat/indictrans2-indic-en-1B')
AutoModelForSeq2SeqLM.from_pretrained('ai4bharat/indictrans2-en-indic-1B')
"
```

**Storage requirements:**
- indictrans2-indic-en-1B: ~2GB
- indictrans2-en-indic-1B: ~2GB
- **Total: ~4GB for full Indic↔Indic support**

## Testing

### Test Case 1: Indic→English (Direct)

```bash
$ ./prepare-job.sh in/hindi.mp4 --subtitle -s hi -t en
```

**Expected:**
- ✅ English subtitles generated
- ✅ Translation uses indictrans2-indic-en model
- ✅ High quality translation

### Test Case 2: Indic→Indic (Pivot)

```bash
$ ./prepare-job.sh in/hindi.mp4 --subtitle -s hi -t gu
```

**Expected (current):**
- ⚠️ Warning: Model not available
- ⚠️ Returns source text (Hindi)
- ℹ️ User informed about limitation

**Expected (after full implementation):**
- ✅ Step 1: hi→en translation
- ✅ Step 2: en→gu translation
- ✅ Gujarati subtitles generated

### Test Case 3: Multiple Targets

```bash
$ ./prepare-job.sh in/hindi.mp4 --subtitle -s hi -t en,gu,ta
```

**Expected:**
- ✅ en: Direct translation (works)
- ⚠️ gu: Pivot needed (partial)
- ⚠️ ta: Pivot needed (partial)

## Recommendations

### Short Term (Current)

1. ✅ **Clear logging** - inform users about limitations
2. ✅ **Fallback behavior** - return source text for unsupported pairs
3. ✅ **Documentation** - explain what works and what doesn't

### Medium Term (Next Sprint)

1. **Install en→indic model** in bootstrap
2. **Implement two-step translation** in translator.py
3. **Test with multiple language pairs**
4. **Update documentation** with full support matrix

### Long Term (Future)

1. **Optimize model loading** (load only when needed)
2. **Cache intermediate translations** (en pivot)
3. **Support custom translation services** (Google, DeepL, etc.)
4. **Add quality metrics** (BLEU scores, user ratings)

## Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **Problem** | ✅ Identified | Indic→Indic not directly supported |
| **Root cause** | ✅ Understood | Separate models for each direction |
| **Workaround** | ✅ Implemented | Fallback to source text |
| **Full solution** | ⚠️ Pending | Requires second model installation |
| **Documentation** | ✅ Complete | This document |
| **User impact** | ⚠️ Moderate | Gets source text instead of translation |

**Next Steps:**
1. Decide: Install second model or keep fallback?
2. If install: Add to bootstrap script
3. If fallback: Enhance user messaging
4. Update README with language support matrix

---

**Status:** ⚠️ PARTIAL FIX - Fallback implemented, full solution pending  
**Impact:** Users requesting Indic→Indic get source text with clear warnings  
**Action:** Decide on full implementation timeline
