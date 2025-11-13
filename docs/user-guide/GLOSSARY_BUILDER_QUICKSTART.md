# Glossary-Builder Quick Start Guide

## What It Does

The glossary-builder automatically generates a film-specific glossary by:
- Mining the ASR transcript for character names and proper nouns
- Fetching cast/crew from TMDB (if API key provided)
- Merging with the master Hinglish glossary
- Caching results for reuse

## Usage

### Default (Automatic)

The glossary-builder runs automatically after ASR transcription:

```bash
# Standard pipeline run
./prepare-job.sh in/movie.mp4
./run_pipeline.sh --job <job-id>

# Check the generated glossary
cat out/<job-id>/glossary/film_glossary.tsv
cat out/<job-id>/glossary/film_profile.json | jq .
```

### With TMDB Integration

Set your TMDB API key to get cast/crew names:

```bash
# Add to .env or export
export TMDB_API_KEY=your_api_key_here

# Run pipeline
./prepare-job.sh in/movie.mp4
./run_pipeline.sh --job <job-id>
```

Get a free API key at: https://www.themoviedb.org/settings/api

### Standalone Execution

Run glossary-builder independently:

```bash
docker compose run --rm glossary-builder \
  --job-dir /app/out/2025/11/10/1/20251110-0001 \
  --title "Jaane Tu Ya Jaane Na" \
  --year 2008 \
  --tmdb-id 86627 \
  --master /app/glossary/hinglish_master.tsv \
  --prompts /app/prompts
```

## Configuration

Edit `config/.env.pipeline`:

```bash
# Enable/disable
GLOSSARY_ENABLE=true

# Data sources (comma-separated)
GLOSSARY_SEED_SOURCES=asr,tmdb

# Quality threshold (0.0-1.0)
GLOSSARY_MIN_CONF=0.55

# Paths
GLOSSARY_MASTER=glossary/hinglish_master.tsv
GLOSSARY_PROMPTS_DIR=prompts
GLOSSARY_CACHE_DIR=glossary/cache
```

## Outputs

Three files are generated in `out/<job-id>/glossary/`:

### 1. film_glossary.tsv

Merged glossary with all terms:

```tsv
term	script	rom	hi	type	english	do_not_translate	capitalize	example_hi	example_en	aliases	source	confidence
yaar	rom	yaar		idiom	dude	false	false			dude|man|buddy	manual:master	1.0
Rajesh Kumar	rom	Rajesh Kumar		character	Rajesh Kumar	true	true		Played by Actor	Aditi Rao	tmdb:cast	0.95
Mumbai	rom	Mumbai		place	Mumbai	true	true	I live in Mumbai		Bombay	asr:frequency	0.8
```

### 2. film_profile.json

Film metadata and statistics:

```json
{
  "title": "Jaane Tu Ya Jaane Na",
  "year": "2008",
  "tmdb_id": "86627",
  "cast": [
    {"name": "Imran Khan", "character": "Jai Singh Rathore"},
    {"name": "Genelia D'Souza", "character": "Aditi Mahant"}
  ],
  "statistics": {
    "glossary_entries": 245,
    "asr_segments": 1823,
    "total_duration_seconds": 7200
  },
  "glossary_breakdown": {
    "idiom": 120,
    "character": 25,
    "place": 15,
    "candidate": 85
  }
}
```

### 3. coverage_report.json

Quality metrics:

```json
{
  "total_segments": 1823,
  "segments_with_glossary_terms": 1456,
  "coverage_pct": 79.88,
  "terms_used": {
    "yaar": 45,
    "bhai": 32,
    "Mumbai": 18
  },
  "terms_unused": ["Goa", "Delhi"],
  "unknown_term_candidates": ["New Term 1", "New Term 2"]
}
```

## Caching

Glossaries are cached for reuse:

```bash
# First run generates glossary
./run_pipeline.sh --job job1  # Same film
# Cache created at: glossary/cache/jaane-tu-ya-jaane-na-2008.tsv

# Second run reuses cache
./run_pipeline.sh --job job2  # Same film, different take
# Loads from cache (faster)

# Force rebuild
docker compose run --rm glossary-builder \
  --job-dir /app/out/job3 \
  --title "Film" \
  --year 2008 \
  --force-rebuild
```

## Disable Glossary Builder

To skip the stage:

```bash
# In config/.env.pipeline
GLOSSARY_ENABLE=false

# Or temporarily
./run_pipeline.sh --job <job-id> --stages asr subtitle_gen mux
```

## Troubleshooting

### No terms extracted from ASR
- Check that ASR stage completed successfully
- Verify ASR JSON files exist in `out/<job-id>/asr/`
- Lower min confidence: `GLOSSARY_MIN_CONF=0.3`

### TMDB integration not working
- Set `TMDB_API_KEY` environment variable
- Check TMDB ID is correct (from TMDB stage output)
- Verify network connectivity

### Glossary not being used in translation
- Future feature: Glossary enforcement in subtitle-gen
- Currently generates glossary only (enforcement coming soon)

## Advanced Usage

### Custom Film Prompts

Create a film-specific prompt file:

```bash
# prompts/jaane-tu-2008.txt
# Custom terms for this film
Meow - character nickname (do not translate)
Rats - character nickname (do not translate)
```

The builder will load and process these prompts.

### Master Glossary Updates

Edit `glossary/hinglish_master.tsv` to add permanent terms:

```tsv
term	script	rom	hi	type	english	do_not_translate	capitalize	...
naya_term	rom	naya_term		idiom	new meaning	false	false	...
```

Rebuild to apply:
```bash
rm glossary/cache/*  # Clear cache
./run_pipeline.sh --job <job-id>
```

## Integration with Other Stages

The glossary is designed to be used by:

- **pre-ner**: Pre-normalization before ASR
- **subtitle-gen**: Enforce glossary choices in output
- **second-pass-translation**: Provide context hints
- **post-ner**: Validate entity consistency

Integration code coming in future updates.

## Next Steps

1. Build the image: `./scripts/build-all-images.sh`
2. Process a film: `./prepare-job.sh in/movie.mp4`
3. Check the glossary: `cat out/<job>/glossary/film_glossary.tsv`
4. Review coverage: `cat out/<job>/glossary/coverage_report.json`
5. Refine master glossary based on candidates
6. Repeat for more films (caching speeds up reruns)

## Support

See full documentation:
- `docker/glossary-builder/README.md` - Detailed usage
- `GLOSSARY-INTEGRATION.md` - Architecture design
- `GLOSSARY_BUILDER_IMPLEMENTATION.md` - Implementation details
