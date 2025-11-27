# Phase 1 Quick Start Guide

## Test Phase 1 Implementation

```bash
# Activate environment
source .venv-common/bin/activate

# Run integration test
python test_phase1.py
```

## Fetch Movie Metadata

```bash
# Example: Jaane Tu Ya Jaane Na
python scripts/fetch_tmdb_metadata.py \
    --title "Jaane Tu Ya Jaane Na" \
    --year 2008 \
    --output test_output/glossary.yaml

# Example: 3 Idiots (JSON format)
python scripts/fetch_tmdb_metadata.py \
    --title "3 Idiots" \
    --year 2009 \
    --output test_output/3idiots.json \
    --format json
```

## Use in Python

### TMDB Client

```python
from shared.tmdb_client import TMDBClient, load_api_key

# Initialize
api_key = load_api_key()
client = TMDBClient(api_key)

# Search movie
movie = client.search_movie("Movie Title", year=2008)
print(f"Found: {movie['title']} (ID: {movie['id']})")

# Get metadata
metadata = client.get_movie_metadata(movie['id'])
print(f"Cast: {len(metadata['cast'])} members")
print(f"Crew: {len(metadata['crew'])} members")
```

### Glossary Generator

```python
from shared.glossary_generator import GlossaryGenerator

# Initialize with TMDB metadata
generator = GlossaryGenerator(metadata)

# Generate standard glossary
glossary = generator.generate()
print(f"Generated {len(glossary)} entries")

# Generate ASR glossary (flat list)
asr_terms = generator.generate_for_asr()
print(f"ASR terms: {len(asr_terms)}")

# Generate translation glossary
trans_glossary = generator.generate_for_translation()
print(f"Translation mappings: {len(trans_glossary)}")

# Save to file
generator.save_yaml(Path("output/glossary.yaml"))
generator.save_json(Path("output/glossary.json"))
generator.save_csv(Path("output/glossary.csv"))
```

### NER Corrector

```python
from shared.ner_corrector import NERCorrector

# Initialize with TMDB metadata
corrector = NERCorrector(metadata, model_name="en_core_web_sm")
corrector.load_model()

# Extract entities
text = "Jai and Aditi are friends in Mumbai."
entities = corrector.extract_entities(text)
for ent in entities:
    print(f"{ent['text']} ({ent['label']})")

# Correct entities
corrected = corrector.correct_text(text)
print(f"Corrected: {corrected}")

# Validate entities
validations = corrector.validate_entities(text)
for val in validations:
    if val['needs_correction']:
        print(f"⚠ {val['original']} -> {val['suggested']}")
```

## Module Files

- `shared/tmdb_client.py` - TMDB API wrapper
- `shared/ner_corrector.py` - NER-based correction
- `shared/glossary_generator.py` - Glossary generation
- `test_phase1.py` - Integration test

## Dependencies

All installed in `.venv-common`:
- tmdbv3api
- spacy + en_core_web_sm
- cachetools
- tqdm
- pyyaml

## Status

✅ Phase 1 Week 1 Complete
📋 Next: Week 2 - Pipeline Integration
