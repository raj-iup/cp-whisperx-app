# Glossary System - Full Integration Guide

## Overview

The Hinglish Glossary System is now fully integrated into the CP-WhisperX-App pipeline, providing context-aware terminology substitution for Hinglish→English subtitle translation. This dramatically improves consistency and cultural accuracy in subtitle generation.

## Integration Status: ✅ COMPLETE

### What's Integrated

1. **Bootstrap Scripts** (`scripts/bootstrap.sh`, `scripts/bootstrap.ps1`)
   - ✅ Validates glossary directory structure
   - ✅ Checks for master TSV file
   - ✅ Counts available movie prompts
   - ✅ Tests glossary module loading
   - ✅ Provides setup guidance

2. **Prepare-Job Scripts** (`prepare-job.sh`, `prepare-job.ps1`, `scripts/prepare-job.py`)
   - ✅ Includes glossary settings in job `.env` files
   - ✅ Auto-detects movie-specific prompts based on filename
   - ✅ Logs glossary configuration status
   - ✅ Provides guidance for adding prompts

3. **Configuration Template** (`config/.env.pipeline`)
   - ✅ `GLOSSARY_ENABLED=true` (default on)
   - ✅ `GLOSSARY_PATH=glossary/hinglish_master.tsv`
   - ✅ `GLOSSARY_STRATEGY=first` (use first option by default)
   - ✅ `FILM_PROMPT_PATH=` (auto-detected per job)

4. **Pipeline Orchestrator** (`scripts/pipeline.py`)
   - ✅ Already loads config from job `.env` file
   - ✅ Passes settings to subtitle-gen stage
   - ✅ No changes needed (works via config)

5. **Subtitle Generation** (`docker/subtitle-gen/subtitle_gen.py`)
   - ✅ Loads glossary if enabled
   - ✅ Applies term substitutions to all segments
   - ✅ Logs statistics (terms applied)
   - ✅ Handles missing glossary gracefully

6. **Glossary Module** (`shared/glossary.py`)
   - ✅ HinglishGlossary class with TSV loading
   - ✅ Term substitution with case preservation
   - ✅ Context-aware selection support
   - ✅ Statistics and validation methods

## Movie-Specific Prompts

We've created comprehensive prompts for iconic Bollywood films across decades:

### 1980s
- ✅ **Laawaris (1981)** - Amitabh, street drama, angry young man
- ✅ **Satte Pe Satta (1982)** - Rural to urban transformation comedy
- ✅ **Inquilaab (1984)** - Revolutionary, labor union politics

### 1990s
- ✅ **Andaz Apna Apna (1994)** - Slapstick comedy, Hinglish punchlines
- ✅ **Dilwale Dulhania Le Jayenge (1995)** - NRI romance, family values
- (existing) **Dil Chahta Hai (2001)** - Urban youth, friend group

### 2000s
- ✅ **Hera Pheri (2000)** - Comedy, Babu Bhaiya's iconic style
- ✅ **Lagaan (2001)** - Period drama, British Raj, cricket
- ✅ **Rang De Basanti (2006)** - Political awakening, youth revolution
- (existing) **Jaane Tu Ya Jaane Na (2008)** - College friends, rom-com
- ✅ **3 Idiots (2009)** - Engineering college, education system

### 2010s
- ✅ **Zindagi Na Milegi Dobara (2011)** - Spain bachelor trip, self-discovery
- ✅ **Gangs of Wasseypur (2012)** - Gritty Bihar crime saga
- ✅ **Queen (2013)** - Solo female travel, empowerment
- ✅ **Dangal (2016)** - Haryanvi wrestling, feminist sports drama
- ✅ **Tumbbad (2018)** - Horror-fantasy, folklore, greed

### 2020s
- ✅ **Gully Boy (2019)** - Mumbai hip-hop, street rap culture
- ✅ **Shershaah (2021)** - Military biopic, Kargil War
- ✅ **Gehraiyaan (2022)** - Urban psychological drama, affair

## How to Use

### For Users

1. **Automatic (Default)**
   ```bash
   # Glossary is enabled by default
   ./prepare-job.sh path/to/movie.mp4
   ./run_pipeline.sh -j <job-id>
   ```

2. **Check Status During Bootstrap**
   ```bash
   ./scripts/bootstrap.sh
   # Look for "GLOSSARY SYSTEM VALIDATION" section
   ```

3. **Verify in Job Preparation**
   ```bash
   ./prepare-job.sh Dangal_2016.mp4
   # Check logs for:
   # "Glossary Configuration:"
   # "✓ Master glossary: glossary/hinglish_master.tsv"
   # "✓ Movie prompt: dangal_2016.txt"
   ```

### For Developers

1. **Add New Movie Prompts**
   ```bash
   # Create file: glossary/prompts/<film_title>_<year>.txt
   
   Film: Movie Name (Year)
   Director: Name
   Stars: Cast
   Setting: Location, era, context
   Tone: Comedy/Drama/etc
   Language: Hindi-English patterns
   
   Characters:
   - Name (male/female): Description
   
   Key Terms:
   - "yaar" → "dude" (usage context)
   - "ji" → "sir/ma'am" (respect patterns)
   
   Translation Notes:
   - Specific guidance for this film
   - Catchphrases to preserve
   - Cultural context
   ```

2. **Add Glossary Terms**
   ```bash
   # Edit: glossary/hinglish_master.tsv
   # Format: source<TAB>preferred_english<TAB>notes<TAB>context
   
   yaar	dude|man	Use dude for young males	casual
   ji	sir|ma'am|	Honorific suffix	honorific
   ```

3. **Test Glossary Loading**
   ```python
   from shared.glossary import HinglishGlossary
   
   glossary = HinglishGlossary("glossary/hinglish_master.tsv")
   text = "Hey yaar, kya scene hai?"
   result = glossary.apply(text)
   print(result)  # "Hey dude, what's up?"
   ```

## Configuration Reference

### Environment Variables (in `.env` files)

```bash
# Enable/disable glossary system
GLOSSARY_ENABLED=true

# Path to master glossary TSV
GLOSSARY_PATH=glossary/hinglish_master.tsv

# Term selection strategy: 'first', 'context', 'ml' (future)
GLOSSARY_STRATEGY=first

# Path to movie-specific prompt (auto-detected or manual)
FILM_PROMPT_PATH=glossary/prompts/dangal_2016.txt
```

### Auto-Detection Logic

When you prepare a job with `prepare-job.sh movie.mp4`, the system:
1. Extracts filename stem (e.g., "dangal_2016")
2. Searches `glossary/prompts/` for matching `.txt` files
3. If found, sets `FILM_PROMPT_PATH` automatically
4. Logs the detection result

## Architecture

```
User runs prepare-job.sh
         ↓
prepare-job.py creates job
         ↓
Copies config/.env.pipeline template
         ↓
Adds GLOSSARY_* settings
         ↓
Auto-detects movie prompt
         ↓
Saves to out/YYYY/MM/DD/USER/JOB/.env
         ↓
User runs pipeline
         ↓
pipeline.py loads job .env
         ↓
Executes subtitle-gen stage
         ↓
subtitle_gen.py loads glossary
         ↓
Applies term substitutions
         ↓
Generates final .srt with improved terms
```

## Statistics & Validation

The glossary system tracks:
- Total terms in glossary
- Terms applied in subtitle generation
- Terms skipped (no match)
- Available movie prompts

View during job execution:
```
[INFO] Loading glossary from: glossary/hinglish_master.tsv
[INFO] Loaded 150 glossary terms
[INFO] Glossary applied: 243 substitutions
[INFO]   Total terms in glossary: 150
```

## Future Enhancements

From `IMPROVEMENT-PLAN.md` Step 8:
- [ ] Context-aware term selection (analyze surrounding text)
- [ ] ML-based term selection based on character/scene
- [ ] Per-character speaking style profiles
- [ ] Regional variant support (Mumbai vs Delhi slang)
- [ ] Frequency-based term learning

## Benefits

1. **Consistency**: Same Hinglish term always translates consistently
2. **Cultural Accuracy**: Preserves intent (yaar→dude, not yaar→friend)
3. **Context Awareness**: Movie prompts guide appropriate choices
4. **Terminology Coverage**: 98%+ consistency target (from improvement plan)
5. **Readability**: Natural-sounding English subtitles

## Troubleshooting

**Q: Glossary not found during job run?**
```bash
# Check file exists
ls -la glossary/hinglish_master.tsv

# Verify bootstrap completed
./scripts/bootstrap.sh
```

**Q: Movie prompt not auto-detected?**
```bash
# Filename must match prompt name
# Movie: "Dangal (2016).mp4"
# Prompt: "dangal_2016.txt" ✓

# Or set manually in job .env:
FILM_PROMPT_PATH=glossary/prompts/dangal_2016.txt
```

**Q: Want to disable glossary temporarily?**
```bash
# Edit job .env file:
GLOSSARY_ENABLED=false
```

## References

- `glossary/README.md` - Detailed glossary system documentation
- `IMPROVEMENT-PLAN.md` - Step 8: Hinglish→English Glossary
- `shared/glossary.py` - Implementation code
- `docker/subtitle-gen/subtitle_gen.py` - Integration point

## Credits

Based on IMPROVEMENT-PLAN.md Step 8 for context-aware Hinglish subtitle generation.
Movie prompts created for iconic Bollywood films from 1980s-2020s.
