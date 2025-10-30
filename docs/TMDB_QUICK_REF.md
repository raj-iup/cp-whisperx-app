# TMDB Stage - Quick Reference

## ✅ Problem Fixed

**Before**: `tmdb_data.json` had only basic title/year with empty arrays
**After**: Full TMDB API integration with comprehensive metadata

## 🚀 Quick Start

### Without API Key (Fallback Mode)
```bash
# Works immediately, no setup needed
python native/scripts/02_tmdb.py \
    --input "in/Movie 2020.mp4" \
    --movie-dir "./out/Movie_2020"
```

### With API Key (Full Features)
```bash
# 1. Get free API key from https://www.themoviedb.org/settings/api
# 2. Set environment variable
export TMDB_API_KEY='your-api-key-here'

# 3. Run the stage
python native/scripts/02_tmdb.py \
    --input "in/Movie 2020.mp4" \
    --movie-dir "./out/Movie_2020"
```

## 📊 What You Get

### Fallback Mode (No API Key)
- ✓ Title and year
- ✓ Basic structure (all fields present)
- ✓ Works offline
- ❌ No cast/crew/genres

### API Mode (With Key)
- ✓ 20+ cast members with characters
- ✓ Directors, writers, producers
- ✓ Plot summary and tagline
- ✓ Genres, keywords, languages
- ✓ Runtime, rating, popularity
- ✓ IMDB ID for cross-reference
- ✓ Poster and backdrop URLs

## 🔧 Configuration Options

### Option 1: Environment Variable (Recommended)
```bash
export TMDB_API_KEY='your-key'
```

### Option 2: Config File
Add to `config/.env`:
```
TMDB_API_KEY=your-key
```

### Option 3: Secrets File
Add to `config/secrets.json`:
```json
{
  "tmdb_api_key": "your-key"
}
```

## 📝 Output Verification

```bash
# Check the output file
cat out/Movie_2020/metadata/tmdb_data.json

# Should contain:
# - Non-null values for key fields
# - Populated cast array (with API key)
# - data_source: "tmdb_api" or "fallback"
```

## 🔍 Troubleshooting

### File is still empty or has placeholder data
✓ API key not set → Export TMDB_API_KEY
✓ Wrong API key → Regenerate on TMDB website
✓ Network issues → Check internet connection

### "Invalid API key" error
✓ Copy the correct key (32 character hex string)
✓ Use v3 API key, not v4 token
✓ Check for spaces or quotes in the key

### Movie not found
✓ Check spelling and year
✓ Search on TMDB website first
✓ Will fall back to basic data automatically

## 📚 Documentation

- **Setup Guide**: `docs/TMDB_API_SETUP.md`
- **Test Script**: `native/scripts/test_tmdb.py`
- **Implementation**: `native/utils/tmdb_fetcher.py`

## 🎯 Benefits for Pipeline

1. **Pre-NER Stage**: Uses cast names for entity recognition
2. **ASR Stage**: Plot context improves transcription accuracy
3. **Post-NER Stage**: Corrects entity names using TMDB data
4. **Metadata**: Enriches output with comprehensive movie info

## ✨ Features

- ✅ Works with or without API key
- ✅ Automatic fallback on errors
- ✅ Rate limit handling
- ✅ Network timeout protection
- ✅ Comprehensive logging
- ✅ Multiple filename formats supported
- ✅ Free and unlimited API access
- ✅ Production-ready

---

**Status**: ✅ Fixed and fully functional
**Version**: 1.0
**Last Updated**: 2025-10-29
