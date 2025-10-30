# TMDB API Integration Guide

## Overview

The TMDB (The Movie Database) stage fetches comprehensive movie metadata including:
- Movie title, year, runtime, rating
- Plot summary and tagline
- Cast and crew (actors, directors, writers, producers)
- Genres, keywords, languages
- IMDB ID for cross-referencing
- Poster and backdrop images
- Budget, revenue, popularity metrics

## Getting a TMDB API Key

### Step 1: Create a TMDB Account

1. Visit https://www.themoviedb.org/
2. Click "Join TMDB" in the top right
3. Fill out the registration form
4. Verify your email address

### Step 2: Request an API Key

1. Log in to your TMDB account
2. Go to Settings → API (https://www.themoviedb.org/settings/api)
3. Click "Request an API Key"
4. Choose "Developer" option
5. Accept the terms of use
6. Fill out the application form:
   - **Type of Use**: Personal/Educational
   - **Application Name**: CP-WhisperX-App
   - **Application URL**: http://localhost (or your project URL)
   - **Application Summary**: "Automated movie transcription and subtitle generation pipeline"

7. Submit the form
8. Your API key will be generated immediately

### Step 3: Copy Your API Key

You'll receive two keys:
- **API Key (v3 auth)**: This is what you need (32 character hex string)
- **API Read Access Token**: Not needed for this project

Copy the **API Key (v3 auth)** - it looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

## Configuring the Pipeline

### Method 1: Environment Variable (Recommended)

Set the API key in your shell:

```bash
# For current session
export TMDB_API_KEY='your-api-key-here'

# Add to ~/.bashrc or ~/.zshrc for persistence
echo "export TMDB_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

### Method 2: Config File

Add to `config/.env`:

```bash
TMDB_API_KEY=your-api-key-here
```

### Method 3: Secrets File

Add to `config/secrets.json`:

```json
{
  "tmdb_api_key": "your-api-key-here",
  "hf_token": "your-huggingface-token"
}
```

## Testing the API Key

Test that your API key works:

```bash
# Quick test with curl
curl "https://api.themoviedb.org/3/search/movie?api_key=YOUR_API_KEY&query=Inception"

# Test with the pipeline
python native/scripts/02_tmdb.py \
    --input "in/Your Movie 2020.mp4" \
    --movie-dir "./out/Your_Movie_2020"
```

You should see:
- ✅ "TMDB API key found - will fetch real data"
- Movie details including cast, crew, genres
- No warnings about fallback data

## What Gets Fetched

With a valid API key, the TMDB stage fetches:

### Basic Info
- Title (original and localized)
- Release year and date
- Runtime in minutes
- IMDB ID
- Overview/plot summary
- Tagline
- Rating (average and vote count)
- Popularity score

### Cast & Crew (Top 20)
- Actor names
- Character names
- Order of appearance
- Director(s)
- Writer(s)
- Producer(s)

### Metadata
- Genres (Drama, Comedy, Action, etc.)
- Keywords/tags
- Spoken languages
- Production countries
- Budget and revenue

### Images
- Poster path
- Backdrop path
- (Full URLs can be constructed for downloading)

## API Usage Limits

TMDB API has generous rate limits:
- **40 requests per 10 seconds** (per IP)
- No daily limit for standard API keys
- More than sufficient for single-movie processing

## Fallback Mode

If no API key is configured, the stage will:
- ✅ Still complete successfully
- ⚠️  Use fallback data (title and year only)
- ℹ️  Log a warning message
- 📝 Mark data source as "fallback"

This ensures the pipeline continues working even without TMDB access.

## Troubleshooting

### "Invalid API key" error

**Problem**: API key is incorrect or revoked

**Solutions**:
1. Double-check the API key (no spaces, complete string)
2. Regenerate the API key on TMDB website
3. Ensure you're using the v3 API key, not the v4 token

### "Too many requests" error

**Problem**: Rate limit exceeded

**Solutions**:
1. Wait 10 seconds and try again
2. Reduce concurrent pipeline runs
3. The pipeline automatically retries with exponential backoff

### "Movie not found" error

**Problem**: TMDB doesn't have the movie in its database

**Solutions**:
1. Check the movie title spelling
2. Try a different year if specified
3. Search manually on TMDB website first
4. Pipeline will fall back to basic data

### API key not being read

**Problem**: Environment variable not set correctly

**Solutions**:
```bash
# Check if it's set
echo $TMDB_API_KEY

# If empty, set it again
export TMDB_API_KEY='your-api-key'

# Make sure to export before running pipeline
export TMDB_API_KEY='your-api-key'
python native/scripts/02_tmdb.py --input "movie.mp4" --movie-dir "./out/movie"
```

## Example Output

### With API Key (Real Data)

```json
{
  "id": 13920,
  "imdb_id": "tt1096124",
  "title": "Jaane Tu... Ya Jaane Na",
  "year": "2008",
  "runtime": 155,
  "overview": "Two best friends realize they're in love...",
  "genres": ["Comedy", "Drama", "Romance"],
  "cast": [
    {"name": "Imran Khan", "character": "Jai Singh Rathore"},
    {"name": "Genelia D'Souza", "character": "Aditi Mahant"},
    ...
  ],
  "directors": [{"name": "Abbas Tyrewala"}],
  "vote_average": 7.2,
  "vote_count": 145,
  "data_source": "tmdb_api"
}
```

### Without API Key (Fallback)

```json
{
  "title": "Jaane Tu Ya Jaane Na",
  "year": "2008",
  "cast": [],
  "crew": [],
  "genres": [],
  "data_source": "fallback",
  "note": "TMDB API key not configured"
}
```

## Privacy & Security

- ✅ API keys are free and not linked to payment
- ✅ No sensitive personal data required
- ✅ Keys can be regenerated anytime
- ⚠️  Don't commit API keys to public repositories
- ✅ Use environment variables or config files (gitignored)

## API Documentation

Full TMDB API documentation:
- Website: https://www.themoviedb.org/
- API Docs: https://developers.themoviedb.org/3
- API Reference: https://developers.themoviedb.org/3/getting-started

## Support

For TMDB API issues:
- Forum: https://www.themoviedb.org/talk
- Support: https://www.themoviedb.org/talk/category/5047951f760ee3318900009a

For pipeline issues:
- Check logs in `logs/tmdb_*.log`
- Review the manifest in `out/<movie>/manifest.json`

---

**Note**: TMDB is a community-maintained database. If a movie is missing or has incorrect data, you can contribute to TMDB to improve it!
