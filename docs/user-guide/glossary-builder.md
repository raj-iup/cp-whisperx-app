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
cat out/<job-id>/03_glossary_load/film_glossary.tsv
cat out/<job-id>/03_glossary_load/film_profile.json | jq .
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

Run glossary-builder stage independently using the pipeline script:

```bash
# Run only the glossary_load stage
./run-pipeline.sh --job <job-id> --stages glossary_load

# Or run via Python directly
cd /Users/rpatel/Projects/cp-whisperx-app
python3 scripts/glossary_builder.py

# Note: Stage requires prior completion of:
#   - Stage 2 (tmdb) for TMDB enrichment data
#   - Stage 6 (asr) for transcript data
```

**Environment Variables:**

The stage uses configuration from `config/.env.pipeline`. You can override specific values:

```bash
# Run with custom configuration
GLOSSARY_SEED_SOURCES=tmdb,master \
GLOSSARY_MIN_CONF=0.75 \
./run-pipeline.sh --job <job-id> --stages glossary_load
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

Three files are generated in `out/<job-id>/03_glossary_load/`:

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
./run-pipeline.sh --job job1  # Same film
# Cache created at: glossary/cache/jaane-tu-ya-jaane-na-2008.json

# Second run reuses cache
./run-pipeline.sh --job job2  # Same film, different take
# Loads from cache (faster)

# Force rebuild by clearing cache
rm glossary/cache/jaane-tu-ya-jaane-na-2008.json
./run-pipeline.sh --job job3

# Or disable caching in config
GLOSSARY_CACHE_ENABLED=false ./run-pipeline.sh --job job3
```

**Note:** The glossary-builder stage runs inline as part of the pipeline (stage 3), not as a separate Docker service.

## Disable Glossary Builder

To skip the stage:

```bash
# In config/.env.pipeline
GLOSSARY_ENABLE=false

# Or temporarily via command line
./run-pipeline.sh --job <job-id> --stages demux,tmdb,asr,subtitle_gen,mux

# The pipeline will skip stage 3 (glossary_load)
```

## Troubleshooting

### No terms extracted from ASR
- Check that ASR stage completed successfully
- Verify ASR JSON files exist in `out/<job-id>/06_asr/`
- Check stage log: `out/<job-id>/03_glossary_load/stage.log`
- Lower min confidence: `GLOSSARY_MIN_CONF=0.3`

### TMDB integration not working
- Set `TMDB_API_KEY` in environment or `config/secrets.json`
- Check TMDB stage completed: `out/<job-id>/02_tmdb/enrichment.json`
- Verify network connectivity
- Check TMDB ID is correct from TMDB stage output

### Glossary not being used in translation
- The glossary-builder generates the glossary (stage 3)
- Glossary enforcement in subtitle-gen (stage 11) is a future feature
- Currently generates reference glossary for manual use

### Stage fails or skips
- Check prerequisites: ASR stage must complete first
- Verify configuration: `GLOSSARY_ENABLE=true`
- Check stage manifest: `out/<job-id>/03_glossary_load/manifest.json`
- Review error messages in stage log

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
source	preferred_english	notes	context
yaar	dude|man|buddy	Use "dude" for young male	casual
naya_term	new meaning	Description of usage	category
```

**Format:** Tab-separated values with 4 columns:
- `source`: Hindi/Hinglish term
- `preferred_english`: Translation options (pipe-separated)
- `notes`: Usage guidance
- `context`: Category/context tag

**Apply changes:**
```bash
# Clear cache to pick up new terms
rm glossary/cache/*.json

# Run pipeline to regenerate glossary
./run-pipeline.sh --job <job-id>
```

## Integration with Other Stages

The glossary is designed to be used by:

- **pre-ner**: Pre-normalization before ASR
- **subtitle-gen**: Enforce glossary choices in output
- **second-pass-translation**: Provide context hints
- **post-ner**: Validate entity consistency

Integration code coming in future updates.

## Next Steps

1. Ensure prerequisites: `./bootstrap.sh` (sets up environment)
2. Process a film: `./prepare-job.sh in/movie.mp4`
3. Run pipeline: `./run-pipeline.sh --job <job-id>`
4. Check the glossary: `cat out/<job-id>/03_glossary_load/film_glossary.tsv`
5. Review coverage: `cat out/<job-id>/03_glossary_load/coverage_report.json | jq .`
6. Refine master glossary based on candidates from coverage report
7. Re-run for better results with updated glossary

## Pipeline Architecture

The glossary-builder runs as **Stage 3 (glossary_load)** in the pipeline:

```
Stage 1: demux              → Extract audio
Stage 2: tmdb               → Get film metadata
Stage 3: glossary_load      → ⭐ Build glossary
Stage 4: source_separation  → Separate vocals
Stage 5: pyannote_vad       → Voice detection
Stage 6: asr                → Speech recognition
...
Stage 11: subtitle_generation → Generate subtitles
Stage 12: mux               → Embed subtitles
```

**Note:** The stage is executed inline by `run-pipeline.py`, not as a separate Docker service.

## Support

See related documentation:
- `docs/DEVELOPER_STANDARDS.md` - Development standards
- `docs/GLOSSARY_BUILDER_REC1_IMPLEMENTATION.md` - Implementation details
- `docs/GLOSSARY_CONFIG_ALIGNMENT_REC3.md` - Configuration guide
- `glossary/hinglish_master.tsv` - Master glossary file
