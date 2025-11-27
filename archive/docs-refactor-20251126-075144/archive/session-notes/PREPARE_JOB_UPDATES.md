# prepare-job.sh Updates - 2025-11-21

## Changes Made

### 1. Fixed Argument Parsing
**Problem:** Shell script wasn't recognizing `--media` flag
**Solution:** Added proper `--media` parameter handling

### 2. Auto-Enable Source Separation for Indic Languages
**Problem:** User had to manually specify `--source-separation` every time
**Solution:** Automatically enable source separation for all Indic language content

### 3. Updated Command Syntax
**Old syntax:**
```bash
./prepare-job.sh movie.mp4 --transcribe --source-language hi
```

**New syntax (both work):**
```bash
# New explicit syntax
./prepare-job.sh --media movie.mp4 --workflow transcribe --source-language hi

# Old syntax still supported for backward compatibility
./prepare-job.sh movie.mp4 --transcribe --source-language hi
```

---

## Auto-Enabled Source Separation

### Indic Languages (Auto-Enabled)
Source separation is **automatically enabled** for these languages:
- Hindi (hi), Tamil (ta), Telugu (te)
- Bengali (bn), Gujarati (gu), Kannada (kn)
- Malayalam (ml), Marathi (mr), Punjabi (pa)
- Urdu (ur), Assamese (as), Odia (or)
- Nepali (ne), Sindhi (sd), Sinhala (si)
- Sanskrit (sa), Kashmiri (ks), Dogri (doi)
- Manipuri (mni), Konkani (kok), Maithili (mai)
- Santali (sat)

### Why Auto-Enable?
- **Bollywood movies** typically have heavy background music
- **Indian content** often has songs mixed with dialogue
- **Better accuracy** with source separation for music-heavy content
- **No manual flag needed** - just works!

---

## Usage Examples

### Basic Usage (Source Separation Auto-Enabled)
```bash
# Hindi movie - source separation enabled automatically
./prepare-job.sh --media "in/movie.mp4" \
                 --workflow subtitle \
                 --source-lang hi \
                 --target-langs en,gu

# Tamil content - auto-enabled too
./prepare-job.sh --media "in/tamil_movie.mp4" \
                 --workflow transcribe \
                 --source-lang ta
```

### With Time Clipping
```bash
./prepare-job.sh --media "in/Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:01:30" --end "00:05:30" \
                 --source-lang hi --target-langs en,gu \
                 --workflow subtitle

# Source separation: ✓ AUTO-ENABLED for Hindi
```

### Custom Quality (Optional)
```bash
# Fast quality for testing
./prepare-job.sh --media "in/movie.mp4" \
                 --workflow subtitle \
                 --source-lang hi --target-langs en \
                 --separation-quality fast

# High quality for production
./prepare-job.sh --media "in/movie.mp4" \
                 --workflow subtitle \
                 --source-lang hi --target-langs en \
                 --separation-quality quality
```

### Non-Indic Languages (No Auto-Enable)
```bash
# English content - source separation NOT auto-enabled
./prepare-job.sh --media "in/english_movie.mp4" \
                 --workflow transcribe \
                 --source-lang en

# Manually enable if needed
./prepare-job.sh --media "in/english_movie.mp4" \
                 --workflow transcribe \
                 --source-lang en \
                 --source-separation
```

---

## Configuration

### Source Separation Settings
- **Default Quality:** `balanced` (good balance of speed and quality)
- **Available Options:** `fast`, `balanced`, `quality`
- **Auto-Enable Logic:** Detected by source language code

### Override Auto-Enable (Not Recommended)
Currently auto-enabled for all Indic languages. To disable, edit:
```bash
# In prepare-job.sh, line ~306
# Comment out or modify the auto-enable section
```

---

## Benefits

### Before (Manual Flag)
```bash
./prepare-job.sh movie.mp4 --workflow subtitle \
                 --source-lang hi --target-langs en \
                 --source-separation  # ← Had to remember this!
```

### After (Auto-Enabled)
```bash
./prepare-job.sh --media movie.mp4 --workflow subtitle \
                 --source-lang hi --target-langs en
# Source separation enabled automatically! 🎉
```

---

## Log Output

When running, you'll see:
```
[INFO] Auto-enabling source separation for Indic language content
[INFO] Source separation: enabled (balanced quality)
```

In job preparation output:
```
🎵 Source separation: ENABLED (balanced quality)
   Background music will be removed from audio
```

---

## Backward Compatibility

### Old Command Format Still Works
```bash
# Old style (still supported)
./prepare-job.sh "in/movie.mp4" --transcribe --source-language hi

# New style (recommended)
./prepare-job.sh --media "in/movie.mp4" --workflow transcribe --source-lang hi

# Both work!
```

### Old Flags Supported
- `--transcribe` → `--workflow transcribe`
- `--translate` → `--workflow translate`
- `--subtitle` → `--workflow subtitle`
- `--source-language` / `-s` → works
- `--target-language` / `-t` → works
- `--start-time` → `--start` (both work)
- `--end-time` → `--end` (both work)

---

## Testing

### Verify Auto-Enable
```bash
# Run job preparation
./prepare-job.sh --media "in/hindi_movie.mp4" \
                 --workflow transcribe \
                 --source-lang hi

# Check log output for:
# [INFO] Auto-enabling source separation for Indic language content
```

### Check Job Config
```bash
# View generated config
cat out/2025/*/job.json | jq '.source_separation'

# Should show:
# {
#   "enabled": true,
#   "quality": "balanced"
# }
```

---

## Summary of Changes

| Change | Before | After |
|--------|--------|-------|
| **Argument Parsing** | Broken with `--media` | Fixed |
| **Source Separation** | Manual flag required | Auto-enabled for Indic |
| **Command Syntax** | Positional only | Named `--media` supported |
| **Python Exec** | `python` | `python3` |
| **Quality Default** | N/A | `balanced` |

---

## Files Modified

1. **prepare-job.sh**
   - Added `--media` parameter handling
   - Added `--workflow` parameter
   - Added auto-enable logic for Indic languages
   - Added `--source-separation` and `--separation-quality` flags
   - Changed `python` to `python3`
   - Added backward compatibility aliases

---

## Status

✅ **COMPLETE** and **TESTED**

**Test Command:**
```bash
./prepare-job.sh --media "in/Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:01:30" --end "00:05:30" \
                 --source-lang hi --target-langs en,gu \
                 --workflow subtitle
```

**Result:** Source separation auto-enabled! 🎉

---

**Date:** 2025-11-21
**Impact:** User-friendly for Bollywood/Indic content
**Breaking Changes:** None (backward compatible)
