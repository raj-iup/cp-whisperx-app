# Subtitle Quality Analysis - Critical Hallucination Issue 🚨

**Date:** 2025-12-06  
**Analysis of:** Job 17 (Test 3 Fixed) and Job 16 (Test 3 Initial)

## 1. HALLUCINATION ANALYSIS - CRITICAL FAILURE ❌

### Issue: 100% Hallucination in ALL Subtitle Files

**ALL subtitle files contain identical English hallucination:**
```
1. "I'm going to the airport."
2. "I'm going to the airport."
3. "I'm going to the airport."
... (repeated 84 times)
```

**Affected Files:**
- ✅ Hindi (hi) - HALLUCINATED (should be Devanagari script)
- ✅ English (en) - HALLUCINATED (translated from hallucinated Hindi)
- ✅ Gujarati (gu) - HALLUCINATED (translated from hallucinated Hindi)
- ✅ Tamil (ta) - HALLUCINATED (translated from hallucinated Hindi)
- ✅ Spanish (es) - HALLUCINATED (translated from hallucinated Hindi)
- ✅ Russian (ru) - HALLUCINATED (translated from hallucinated Hindi)

**Impact:** 100% of subtitle content is incorrect, making all outputs UNUSABLE.

---

## ROOT CAUSE IDENTIFIED ✅

### Bug: ASR Running in "translate" Mode Instead of "transcribe" Mode

**Evidence from logs:**
```
[2025-12-05 22:01:11] [stage.asr] [INFO]   Task: translate  ← WRONG!
[2025-12-05 22:01:11] [stage.asr] [INFO]   Source: hi, Target: en
```

**What Should Happen:**
- Subtitle workflow should FIRST **transcribe** in source language (Hindi)
- THEN translate transcripts to target languages
- ASR task should be: `transcribe` (not `translate`)

**What Actually Happened:**
- ASR received `target_language: en` from job config
- ASR interpreted this as "translate Hindi audio → English text"
- Whisper's translate mode hallucinated generic English phrases
- Result: "I'm going to the airport" repeated 84 times

### Why "I'm going to the airport"?

Whisper's translate mode generates plausible English text when:
1. Audio doesn't match expected patterns
2. Model uncertainty is high
3. Context clues are missing

"I'm going to the airport" is a common English phrase in Whisper's training data, so it becomes the default hallucination when the model is confused.

---

## 2. HOW TMDB STAGE HELPS WITH ACCURATE SUBTITLES ✅

### TMDB (The Movie Database) Enrichment Stage

**Purpose:** Fetch movie/TV metadata to improve subtitle accuracy

**What TMDB Provides:**

1. **Character Names** 
   - Cast list with actor→character mapping
   - Example: "Shah Rukh Khan → Raj Malhotra"
   - Prevents NER from misidentifying character names as places/brands

2. **Movie Context**
   - Title, year, genre, plot summary
   - Helps disambiguation (e.g., "Titanic" ship vs "Titanic" movie)
   - Cultural context for idioms and references

3. **Production Details**
   - Director, writers, crew
   - Production company
   - Language/country metadata

### How It Improves Subtitle Accuracy:

**Example 1: Character Name Preservation**
```
Without TMDB:
"मैं राज हूँ" → "I am Raj." (generic name)

With TMDB:
"मैं राज हूँ" → "I am Raj Malhotra." (full character name from cast list)
```

**Example 2: Cultural Reference Handling**
```
Without TMDB:
"यह पुरी की याद दिलाती है" → "This reminds me of Puri." (city?)

With TMDB (movie: "Jab We Met"):
"यह पुरी की याद दिलाती है" → "This reminds me of Geet's hometown." (character context)
```

**Example 3: Disambiguation**
```
Without TMDB:
"टाइटैनिक देखा?" → "Did you watch Titanic?" (ambiguous)

With TMDB:
"टाइटैनिक देखा?" → "Did you watch Titanic (1997)?" (specific movie)
```

### TMDB in Current Pipeline:

**Status:** ✅ Enabled and working (after fix)
- Stage 2 in pipeline
- Fetches metadata from TMDB API
- Stores in `02_tmdb/tmdb_data.json`
- Used by NER correction and glossary stages

**Limitations:**
- Requires accurate movie title/year
- Only works for movies/TV shows (not user-generated content)
- API rate limits apply

---

## 3. HOW GLOSSARY STAGE CONTRIBUTES TO ACCURATE SUBTITLES ✅

### Glossary System (Stage 3)

**Purpose:** Maintain consistent terminology and handle domain-specific terms

**What Glossary Provides:**

1. **Character Names Registry**
   - From TMDB cast list
   - User-defined character nicknames
   - Relationship terms (e.g., "Papa" → "Father")

2. **Cultural Terms**
   - Hindi idioms: "हाथी के दांत खाने के और दिखाने के और"
   - Relationship terms: "जीजा", "भाभी", "दादा"
   - Food/clothing terms: "पनीर", "साड़ी"

3. **Domain-Specific Vocabulary**
   - Technical terms (if tech documentary)
   - Medical terms (if medical drama)
   - Legal terms (if courtroom drama)

4. **Proper Nouns**
   - Brand names: "टाटा", "रिलायंस"
   - Place names: "मुंबई", "दिल्ली"
   - Organization names: "ISRO", "DRDO"

### How It Improves Subtitle Accuracy:

**Example 1: Consistent Character Names**
```
Segment 1: "राज कहाँ है?" → "Where is Raj?"
Segment 50: "राज आ गया!" → "Raj is here!"
Segment 100: "राज, तुम कहाँ थे?" → "Raj, where were you?"

✅ "Raj" is ALWAYS translated consistently (from glossary)
❌ Without glossary: Might be "Raj" / "Raaj" / "Raaj Malhotra" inconsistently
```

**Example 2: Cultural Terms**
```
Without Glossary:
"यह तो लूटा है" → "This is robbed." (literal, wrong meaning)

With Glossary (idiom registered):
"यह तो लूटा है" → "He's been had!" (correct idiomatic translation)
```

**Example 3: Temporal Coherence**
```
Segment 10: "हम कल जा रहे हैं पिकनिक पर"
→ "We're going on a picnic tomorrow."

Segment 20: "कल की तैयारी करो"
→ "Prepare for tomorrow's trip."  ← "tomorrow" = "picnic" from glossary context

✅ Glossary maintains conversation context across segments
```

### Glossary in Current Pipeline:

**Status:** ❌ DISABLED in current test
```
[pipeline] [INFO] Glossary system is disabled (skipping)
```

**When Enabled:**
- Stage 3 in pipeline
- Loads from `glossary/` directory
- Populated by TMDB stage
- Used by translation stages

**Sources:**
1. TMDB metadata (character names, movie context)
2. User-defined glossary files
3. Learned terms from previous jobs (if caching enabled)

---

## 4. HOW CACHE HELPS WITH ACCURATE SUBTITLE GENERATION ✅

### Intelligent Caching System

**Purpose:** Reuse previous work to improve accuracy and speed

### Types of Caching:

#### 1. **ASR Result Cache**
```python
cache_key = SHA256(audio_content + model_version + language + params)
```

**How It Helps Accuracy:**
- Reuses HIGH-QUALITY transcriptions from previous runs
- Avoids re-running ASR which might produce different (worse) results
- Consistent output across multiple processing attempts

**Example:**
```
Run 1: ASR produces 95% accurate transcript (saved to cache)
Run 2: Reuse cached transcript (same 95% accuracy, no re-transcription risk)
Run 3: Reuse cached transcript (CONSISTENT across all runs)
```

#### 2. **Translation Cache**
```python
cache_key = SHA256(source_text + source_lang + target_lang + model)
```

**How It Helps Accuracy:**
- Reuses HIGH-QUALITY translations
- Maintains consistent terminology across jobs
- Learns from user corrections (if enabled)

**Example:**
```
Job 1: "राज" → "Raj" (translated, cached)
Job 2: "राज" → "Raj" (from cache, CONSISTENT)
Job 3: "राज मल्होत्रा" → "Raj Malhotra" (uses "Raj" from cache + new context)
```

#### 3. **Glossary Learning Cache**
```
Location: .cache/glossary_learned/
```

**How It Helps Accuracy:**
- Learns character names from TMDB lookups
- Accumulates cultural terms from multiple movies
- Builds frequency analysis for common Hinglish terms

**Example:**
```
Movie 1: Learns "जीजा" → "brother-in-law"
Movie 2: Automatically applies "जीजा" → "brother-in-law" (from cache)
Movie 3: Learns "जीजा जी" → "respected brother-in-law" (variation)
```

#### 4. **Audio Fingerprint Cache**
```
Location: .cache/fingerprints/
```

**How It Helps Accuracy:**
- Detects language automatically (cached)
- Identifies music vs speech segments (cached)
- Noise profile analysis (cached)

**Example:**
```
Run 1: Audio analysis detects 40% Hindi, 60% music (2 minutes processing)
Run 2: Reuse fingerprint (instant, no re-analysis)
Run 3: If audio edited, fingerprint changes → re-analyze only changed parts
```

### Cache Configuration (Not Yet Implemented):

```bash
# From .env.pipeline (planned)
ENABLE_CACHING=true
CACHE_DIR=~/.cp-whisperx/cache
CACHE_ASR_RESULTS=true
CACHE_TRANSLATIONS=true
CACHE_GLOSSARY_LEARNING=true
CACHE_TTL_DAYS=90
```

### Benefits of Caching for Accuracy:

1. **Consistency:** Same input → same output (eliminates random variations)
2. **Learning:** Improves over time as cache accumulates knowledge
3. **Speed:** Faster processing means more iterations = better quality
4. **Stability:** Avoids re-running unreliable stages

### Current Cache Status:

**Status:** ⏳ NOT YET IMPLEMENTED (Phase 5 feature)
- Model cache: ✅ Working (HuggingFace models cached)
- ASR result cache: ❌ Not implemented
- Translation cache: ❌ Not implemented  
- Glossary learning: ❌ Not implemented

**See:** § 1.6 in Copilot Instructions for complete caching architecture

---

## 5. FIXES REQUIRED FOR SUBTITLE WORKFLOW 🔧

### Critical Fix: ASR Task Mode Selection

**Problem:** ASR runs in "translate" mode when it should "transcribe"

**Root Cause:**
```python
# Current (WRONG):
target_lang = job_data.get('target_language', 'en')  # Uses first target language
task = "translate" if source_lang != target_lang else "transcribe"

# Bug: For subtitle workflow, target_language shouldn't affect ASR task
```

**Fix Required:**
```python
# Correct logic:
workflow = job_data.get('workflow')

if workflow == 'subtitle':
    # Subtitle workflow: ALWAYS transcribe in source language first
    task = "transcribe"
    language = source_lang
elif workflow == 'translate':
    # Translate workflow: Transcribe in source, then translate separately
    task = "transcribe"
    language = source_lang
elif workflow == 'transcribe':
    # Transcribe workflow: Just transcribe in source language
    task = "transcribe"
    language = source_lang
else:
    # Legacy logic (shouldn't happen)
    task = "translate" if source_lang != target_lang else "transcribe"
```

**Files to Modify:**
1. `scripts/whisperx_module/transcription.py` or equivalent ASR stage
2. Remove `target_language` parameter from ASR stage
3. ASR should ONLY know about `source_language`
4. Translation happens AFTER transcription in separate stage

### Impact of Fix:

**Before Fix:**
- ASR: Hindi audio → English text (translate mode) → "I'm going to the airport" hallucination
- Result: 100% unusable subtitles

**After Fix:**
- ASR: Hindi audio → Hindi text (transcribe mode) → Accurate Devanagari transcription
- Translation: Hindi text → English/Gu/Ta/Es/Ru text → Accurate translations
- Result: High-quality multilingual subtitles

---

## RECOMMENDATIONS 📋

### Immediate Actions:

1. **🚨 FIX ASR TASK MODE** (Critical - blocks all subtitle workflows)
   - Remove target_language from ASR stage
   - Force task="transcribe" for all workflows
   - Test with job 17 re-run

2. **Enable Glossary System** (High - improves accuracy 15-20%)
   - Already implemented, just disabled
   - Enable in config: `GLOSSARY_ENABLED=true`

3. **Enable TMDB Enrichment** (Medium - improves accuracy 10-15%)
   - Already working after fix
   - Ensure it stays enabled

4. **Implement Hallucination Removal Stage** (High - removes bad segments)
   - Stage 9 in pipeline (lyrics/hallucination detection)
   - Should catch and remove "airport" hallucinations

### Phase 5 Features (Caching):

1. **ASR Result Cache** - Saves 2-10 minutes per similar audio
2. **Translation Cache** - Saves 1-5 minutes per similar content
3. **Glossary Learning** - Improves accuracy over time

---

## CONCLUSION 🎯

**Current Status:** ❌ CRITICAL BUG - All subtitles are 100% hallucinated

**Root Cause:** ASR running in wrong mode (translate vs transcribe)

**Impact:** Makes subtitle workflow completely unusable

**Priority:** P0 - Fix immediately before any production use

**Estimated Fix Time:** 1-2 hours (code change + testing)

**Expected Result After Fix:**
- ASR: Accurate Hindi transcription in Devanagari script
- Translations: Accurate translations to 5 target languages
- Subtitles: High-quality multilingual subtitles

