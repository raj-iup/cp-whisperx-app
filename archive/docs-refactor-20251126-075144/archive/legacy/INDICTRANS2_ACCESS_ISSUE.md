# IndicTrans2 Model Access Issue - Analysis

**Date**: November 20, 2025  
**Time**: 12:22:03  
**Job ID**: job-20251120-rpatel-0003  
**Status**: ⚠️ PARTIAL SUCCESS (English worked, Gujarati failed)

---

## Executive Summary

The IndicTrans2 authentication is **working correctly** - the HuggingFace token is being loaded and passed to the API. However, the user **lacks access to one of the two required models**.

**Translation Job**:
- Source: Hindi (`hi`)
- Targets: English (`en`) + Gujarati (`gu`)

**Results**:
- ✅ **Hindi → English**: Success (uses `indictrans2-indic-en-1B`)
- ❌ **Hindi → Gujarati**: Failed (needs `indictrans2-indic-indic-1B`)

---

## Log Analysis

### Key Log Lines

```
Line 1: [INFO] Using model: ai4bharat/indictrans2-indic-indic-1B
Line 2: [INFO] Translation: hi (hin_Deva) → gu (guj_Gujr)
Line 4: [INFO] Using device: mps
Line 5: [INFO] ✓ HuggingFace token found     ← TOKEN LOADED!
Line 7: [ERROR] AUTHENTICATION ERROR: IndicTrans2 model access denied
```

### What the Log Tells Us

1. **✅ Token is loaded**: Line 5 confirms our fix worked!
2. **✅ Token is passed to API**: The authentication attempt was made
3. **❌ HuggingFace rejected**: User doesn't have access to this specific model

---

## Root Cause

HuggingFace has **two separate IndicTrans2 models**, each requiring **individual access approval**:

### Model 1: Indic → English
- **Model**: `ai4bharat/indictrans2-indic-en-1B`
- **URL**: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
- **User Access**: ✅ **GRANTED** (user can translate Indic → English)
- **Use Cases**: hi→en, ta→en, bn→en, etc.

### Model 2: Indic → Indic
- **Model**: `ai4bharat/indictrans2-indic-indic-1B`
- **URL**: https://huggingface.co/ai4bharat/indictrans2-indic-indic-1B
- **User Access**: ❌ **MISSING** (needs to request access)
- **Use Cases**: hi→gu, hi→ta, ta→te, bn→hi, etc.

---

## Why Separate Access?

HuggingFace treats each model repository as a separate gated resource:

| Model | Purpose | Languages | Access |
|-------|---------|-----------|--------|
| `indictrans2-indic-en-1B` | Indic → English | 22 → 1 | ✅ User has |
| `indictrans2-indic-indic-1B` | Indic → Indic | 22 → 22 | ❌ User needs |

Even though both are "IndicTrans2" models, they are:
- Different repositories
- Different model files
- Different access gates

**Think of it like**: Having access to "Building A" doesn't give you access to "Building B" - you need to request access to each separately.

---

## Solution

### Step 1: Request Access to Indic→Indic Model

**Visit**: https://huggingface.co/ai4bharat/indictrans2-indic-indic-1B

**Action**: Click "**Agree and access repository**"

**Approval Time**: Instant (< 1 minute)

### Step 2: Verify Access Granted

**Check Dashboard**: https://huggingface.co/settings/gated-repos

**Should See**:
```
✓ ai4bharat/indictrans2-indic-en-1B      (Already granted)
✓ ai4bharat/indictrans2-indic-indic-1B   (Newly granted)
```

### Step 3: Re-run Pipeline

```bash
# Re-run the failed job
./run-pipeline.sh -j job-20251120-rpatel-0003

# Or prepare a new job
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu
./run-pipeline.sh -j <new-job-id>
```

### Step 4: Verify Success

**Check logs**:
```bash
tail -f out/2025/11/20/rpatel/3/logs/*indictrans2_gu*.log
```

**Expected Output**:
```
[INFO] Loading IndicTrans2 model: ai4bharat/indictrans2-indic-indic-1B
[INFO] ✓ HuggingFace token found
[INFO] ✓ IndicTrans2 model loaded successfully
[INFO] Translating 123 segments...
[INFO] ✓ Translation complete
```

---

## Current Fallback Behavior

When IndicTrans2 fails, the pipeline automatically falls back to **Whisper translation**:

```
Line 22: [WARNING] Pipeline will fall back to Whisper translation for now.
```

**What This Means**:
- ✅ Pipeline continues (doesn't crash)
- ✅ Gujarati subtitles are still generated
- ⚠️ **Lower quality** translation (Whisper is not optimized for Indic→Indic)

**Quality Comparison**:
- **IndicTrans2 (Indic→Indic)**: ⭐⭐⭐⭐⭐ (Best for Indic languages)
- **Whisper (fallback)**: ⭐⭐⭐ (General purpose, less accurate for Indic)

---

## Workflow Impact

### Current State (Missing indic-indic Access)

| Workflow | Source | Target | Model Used | Status |
|----------|--------|--------|------------|--------|
| Transcribe | Any | - | WhisperX | ✅ Works |
| Translate | Hindi | English | indictrans2-indic-en-1B | ✅ Works |
| Translate | Hindi | Gujarati | ❌ Fallback to Whisper | ⚠️ Works (lower quality) |
| Translate | Hindi | Tamil | ❌ Fallback to Whisper | ⚠️ Works (lower quality) |
| Translate | Tamil | English | indictrans2-indic-en-1B | ✅ Works |
| Translate | Tamil | Telugu | ❌ Fallback to Whisper | ⚠️ Works (lower quality) |

### After Granting Access (Both Models)

| Workflow | Source | Target | Model Used | Status |
|----------|--------|--------|------------|--------|
| Transcribe | Any | - | WhisperX | ✅ Works |
| Translate | Hindi | English | indictrans2-indic-en-1B | ✅ Works |
| Translate | Hindi | Gujarati | indictrans2-indic-indic-1B | ✅ **Works (high quality)** |
| Translate | Hindi | Tamil | indictrans2-indic-indic-1B | ✅ **Works (high quality)** |
| Translate | Tamil | English | indictrans2-indic-en-1B | ✅ Works |
| Translate | Tamil | Telugu | indictrans2-indic-indic-1B | ✅ **Works (high quality)** |

---

## Job Details

**Job Configuration** (`job.json`):
```json
{
  "job_id": "job-20251120-rpatel-0003",
  "workflow": "subtitle",
  "source_language": "hi",
  "target_languages": ["en", "gu"],
  "input_media": ".../Jaane Tu Ya Jaane Na 2008.mp4",
  "title": "Jaane Tu Ya Jaane Na",
  "year": "2008",
  "media_processing": {
    "mode": "clip",
    "start_time": "00:06:00",
    "end_time": "00:08:30"
  }
}
```

**Translation Tasks**:
1. **Hindi → English**: Uses `indictrans2-indic-en-1B` ✅
2. **Hindi → Gujarati**: Uses `indictrans2-indic-indic-1B` ❌ ← BLOCKED

---

## Verification Commands

### Check Current Access
```bash
# Method 1: Via web browser
open https://huggingface.co/settings/gated-repos

# Method 2: Via CLI (if installed)
huggingface-cli whoami
```

### Check Token is Working
```bash
cd /Users/rpatel/Projects/cp-whisperx-app

# Verify token loads
venv/indictrans2/bin/python << 'EOF'
import sys
sys.path.insert(0, 'scripts')
from indictrans2_translator import IndicTrans2Translator

translator = IndicTrans2Translator(source_lang="hi", target_lang="gu")
token = translator._get_hf_token()

if token:
    print(f"✅ Token: {token[:10]}...")
else:
    print("❌ No token")
EOF
```

### Test Model Access (After Granting)
```bash
# Try loading the indic-indic model
venv/indictrans2/bin/python << 'EOF'
from transformers import AutoTokenizer
import json

# Load token
with open('config/secrets.json') as f:
    token = json.load(f)['hf_token']

# Try loading model
try:
    tokenizer = AutoTokenizer.from_pretrained(
        'ai4bharat/indictrans2-indic-indic-1B',
        token=token,
        trust_remote_code=True
    )
    print("✅ Model access granted!")
except Exception as e:
    print(f"❌ Still no access: {e}")
EOF
```

---

## Why the Fix Was Still Necessary

Even though the user still needs to request access, our fix **was essential** because:

1. **Before Fix**: 
   - Token not passed → Generic "access denied" error
   - Confusing: User thought token was missing entirely
   - No way to distinguish between "no token" vs "no access"

2. **After Fix**:
   - Token passed → Specific error from HuggingFace
   - Clear: "✓ Token found" but "access denied"
   - Easy to diagnose: User needs to request model access

**The fix enables proper error diagnosis!**

---

## Related Models That May Need Access

If translating between multiple Indic languages, request access to:

1. **ai4bharat/indictrans2-indic-en-1B**
   - For: Any Indic → English
   - Example: hi→en, ta→en, bn→en, gu→en

2. **ai4bharat/indictrans2-indic-indic-1B**
   - For: Any Indic → Any Indic
   - Example: hi→gu, hi→ta, ta→te, bn→hi

Both are free and instant approval. Request both to enable all translation combinations.

---

## Summary

| Item | Status |
|------|--------|
| **Token Loading** | ✅ Working (our fix successful) |
| **Token Passing** | ✅ Working (passed to HuggingFace API) |
| **indictrans2-indic-en-1B Access** | ✅ User has access |
| **indictrans2-indic-indic-1B Access** | ❌ User needs to request |
| **Hindi → English** | ✅ Working |
| **Hindi → Gujarati** | ⚠️ Fallback to Whisper (lower quality) |

**Action Required**: Request access to `ai4bharat/indictrans2-indic-indic-1B` at https://huggingface.co/ai4bharat/indictrans2-indic-indic-1B

**Expected Time**: < 1 minute for approval

**After Access**: Re-run pipeline for high-quality Indic→Indic translation

---

**Next Steps**:
1. ✅ Our authentication fix is working correctly
2. ⏭️ User: Request access to indictrans2-indic-indic-1B model
3. ⏭️ User: Re-run pipeline after access granted
4. ✅ Expect high-quality Hindi → Gujarati translation
