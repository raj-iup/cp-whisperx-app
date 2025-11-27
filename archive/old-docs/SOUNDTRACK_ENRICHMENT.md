# Soundtrack Enrichment for Song Bias Injection

## Overview

The TMDB enrichment stage now includes soundtrack information fetching to improve ASR accuracy for song titles, artist names, and composer names in Bollywood movies.

## Implementation

### Architecture

1. **TMDB API Integration** - Fetches movie metadata including:
   - Cast and crew
   - Genres
   - External IDs (IMDb ID)

2. **Local Soundtrack Database** - JSON-based database for Bollywood soundtracks:
   - Path: `config/bollywood_soundtracks.json`
   - Contains song titles, artists, and composers
   - Manually curated for accuracy

3. **Enrichment Output** - Creates `enrichment.json` with complete metadata:
   - Cast, crew, and genres
   - Soundtrack tracks with artist/composer information
   - Used by song bias injection stage (Stage 7)

### Components Modified

#### 1. `scripts/tmdb_enrichment.py`

**New Functions:**
- `get_movie_details()` - Fetches detailed movie info including external IDs and genres
- `load_soundtrack_database()` - Loads local soundtrack database
- `get_soundtrack_for_movie()` - Matches movie to soundtrack using multiple strategies

**Enhanced:**
- `TMDBMetadata` dataclass - Added `soundtrack`, `genres`, and `imdb_id` fields
- `enrich_from_tmdb()` - Now includes soundtrack lookup
- `main()` - Saves both `tmdb_data.json` and `enrichment.json`

#### 2. `shared/config.py`

**New Fields:**
- `song_bias_enabled: bool` - Enable/disable song bias injection (default: True)
- `song_bias_fuzzy_threshold: float` - Fuzzy matching threshold (default: 0.80)

#### 3. `scripts/song_bias_injection.py`

**Fixed:**
- Config reading to use `getattr()` instead of dict `.get()`
- API usage to call `correct_segments()` correctly with tuple unpacking

## Soundtrack Database Format

### File: `config/bollywood_soundtracks.json`

```json
{
  "Movie Title (Year)": {
    "title": "Movie Title",
    "year": 2008,
    "imdb_id": "tt1234567",
    "tracks": [
      {
        "title": "Song Title",
        "artist": "Singer Name(s)",
        "composer": "Music Director"
      }
    ]
  }
}
```

### Matching Strategy

The system tries multiple matching approaches (in order):
1. Exact match: `"Movie Title (Year)"`
2. Title-only match: `"Movie Title"`
3. IMDb ID match: Using IMDb ID from TMDB
4. Fuzzy match: Case-insensitive, punctuation-insensitive

### Example Entry

```json
{
  "Jaane Tu... Ya Jaane Na (2008)": {
    "title": "Jaane Tu... Ya Jaane Na",
    "year": 2008,
    "imdb_id": "tt0473367",
    "tracks": [
      {
        "title": "Pappu Can't Dance Saala",
        "artist": "Benny Dayal",
        "composer": "A. R. Rahman"
      },
      {
        "title": "Kabhi Kabhi Aditi",
        "artist": "Rashid Ali",
        "composer": "A. R. Rahman"
      }
    ]
  }
}
```

## Usage

### Automatic Operation

Soundtrack enrichment runs automatically in the TMDB stage (Stage 2):

```bash
# Run pipeline normally - soundtrack data fetched automatically
./run_pipeline.sh -j <job-id>
```

### Adding New Movies

To add soundtrack data for a new movie:

1. Edit `config/bollywood_soundtracks.json`
2. Add entry using the format above
3. Include:
   - Movie title and year
   - IMDb ID (optional but recommended)
   - All soundtrack tracks with titles, artists, and composers

### Verification

Check if soundtrack was loaded:

```bash
# View enrichment data
cat out/<path-to-job>/02_tmdb/enrichment.json | python3 -m json.tool

# Check song bias injection log
cat out/<path-to-job>/logs/07_song_bias_injection_*.log
```

Expected output in log:
```
[INFO] Found 6 songs in soundtrack
[INFO] Loaded 16 song-specific bias terms
[INFO] Applying song bias correction with 16 terms...
```

## Benefits

1. **Improved ASR Accuracy** - Song titles and artist names are correctly transcribed
2. **Better Subtitle Quality** - Proper names maintained in song sequences
3. **Extensible** - Easy to add new movies to the database
4. **No External Dependencies** - Works offline with local database

## Data Sources

For adding new soundtrack data:

- **IMDb** - https://www.imdb.com (manual lookup)
- **MusicBrainz** - https://musicbrainz.org (open database)
- **Gaana/JioSaavn** - Popular Indian music platforms
- **Wikipedia** - Movie soundtrack information

## Troubleshooting

### Soundtrack Not Loading

**Issue:** Log shows "TMDB enrichment file not found"

**Solution:** 
- Ensure TMDB stage ran successfully
- Check `enrichment.json` exists in `02_tmdb/` directory
- Verify `TMDB_API_KEY` is configured in `config/secrets.json`

### No Soundtrack Available

**Issue:** Log shows "Soundtrack: Not available"

**Solution:**
- Add movie to `config/bollywood_soundtracks.json`
- Ensure title/year matches TMDB data exactly
- Consider adding IMDb ID for better matching

### Song Bias Not Applied

**Issue:** No corrections made despite soundtrack loaded

**Possible Causes:**
1. Song titles already correctly transcribed by ASR
2. Song names don't appear in transcript (no musical sequences)
3. Fuzzy matching threshold too strict (adjust `SONG_BIAS_FUZZY_THRESHOLD`)

## Future Enhancements

Potential improvements:

1. **API Integration** - Connect to MusicBrainz or Spotify APIs
2. **Auto-population** - Scrape soundtrack data from public sources
3. **Confidence Scores** - Track correction confidence levels
4. **Multi-language Support** - Handle regional language variations
5. **Lyrics Alignment** - Align transcript with known lyrics

## Related Documentation

- [Song Bias Injection](../scripts/song_bias_injection.py)
- [TMDB Enrichment](../scripts/tmdb_enrichment.py)
- [Bias Injection Core](../scripts/bias_injection_core.py)

## Configuration Reference

```bash
# In job .env file
SONG_BIAS_ENABLED=true                  # Enable song bias injection
SONG_BIAS_FUZZY_THRESHOLD=0.80         # Lower = more lenient matching
```
