# Implementation Roadmap - Remaining Work

## ✅ What's Complete (Foundation)

### Architecture (100%)
- ✅ Complete directory structure
- ✅ Shared utilities module (config, logger, utils)
- ✅ Base Docker image
- ✅ Docker Compose configuration
- ✅ Preflight validation system
- ✅ Pipeline orchestrator
- ✅ Build and deployment scripts
- ✅ Comprehensive documentation

### Working Containers (2/10 = 20%)
- ✅ **demux** - FFmpeg audio extraction (COMPLETE)
- ✅ **mux** - Subtitle embedding (COMPLETE)

## 🔨 What Needs Implementation (8 Containers)

Each container needs:
1. Python script in `docker/<name>/`
2. Dockerfile extending base image
3. Dependencies added to Dockerfile

---

### Container 2: TMDB Metadata Fetch

**Priority:** HIGH  
**Complexity:** LOW  
**Estimated Time:** 1-2 hours

**Files to create:**
```
docker/tmdb/Dockerfile
docker/tmdb/tmdb.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir requests tmdbv3api
```

**Implementation:**
```python
# Pseudocode for tmdb.py
1. Load config (TMDB_API_KEY from secrets)
2. Parse movie title and year from input
3. Search TMDB API
4. Extract: cast, crew, plot, keywords, genres
5. Save to temp/metadata/tmdb_data.json
6. Log results
```

**Input:** Movie title/year from filename
**Output:** `temp/metadata/tmdb_data.json`

---

### Container 3: Pre-ASR NER

**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Estimated Time:** 3-4 hours

**Files to create:**
```
docker/pre-ner/Dockerfile
docker/pre-ner/pre_ner.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir spacy transformers
RUN python -m spacy download en_core_web_trf
```

**Implementation:**
```python
# Pseudocode for pre_ner.py
1. Load TMDB metadata
2. Load spaCy model (en_core_web_trf)
3. Extract entities from plot, cast names
4. Build entity list: PERSON, ORG, GPE, LOC
5. Save to temp/entities/pre_ner.json
6. Generate initial prompt for WhisperX
```

**Input:** `temp/metadata/tmdb_data.json`
**Output:** `temp/entities/pre_ner.json`, `temp/prompts/initial_prompt.txt`

---

### Container 4: Silero VAD

**Priority:** HIGH  
**Complexity:** MEDIUM  
**Estimated Time:** 2-3 hours

**Files to create:**
```
docker/silero-vad/Dockerfile
docker/silero-vad/silero_vad.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir torch torchaudio
```

**Implementation:**
```python
# Pseudocode for silero_vad.py
1. Load audio from temp/audio/
2. Load Silero VAD model
3. Detect speech segments
4. Apply thresholds from config
5. Save segments to temp/vad/silero_segments.json
```

**Input:** `temp/audio/*.wav`
**Output:** `temp/vad/silero_segments.json`

---

### Container 5: PyAnnote VAD

**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Estimated Time:** 2-3 hours

**Files to create:**
```
docker/pyannote-vad/Dockerfile
docker/pyannote-vad/pyannote_vad.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir pyannote.audio torch torchaudio
```

**Implementation:**
```python
# Pseudocode for pyannote_vad.py
1. Load Silero VAD segments
2. Load PyAnnote VAD model
3. Refine boundaries around speech
4. Merge/split based on config thresholds
5. Save refined segments
```

**Input:** `temp/vad/silero_segments.json`, `temp/audio/*.wav`
**Output:** `temp/vad/pyannote_segments.json`

---

### Container 6: PyAnnote Diarization

**Priority:** CRITICAL  
**Complexity:** HIGH  
**Estimated Time:** 4-5 hours

**Files to create:**
```
docker/diarization/Dockerfile
docker/diarization/diarization.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir pyannote.audio torch torchaudio speechbrain
```

**Implementation:**
```python
# Pseudocode for diarization.py
1. Load VAD segments
2. Load PyAnnote diarization model (HF token required)
3. Identify speakers
4. Assign speaker labels (SPEAKER_00, SPEAKER_01, etc.)
5. Save diarization results
```

**Input:** `temp/vad/pyannote_segments.json`, `temp/audio/*.wav`
**Output:** `temp/diarization/speakers.json`

---

### Container 7: WhisperX ASR

**Priority:** CRITICAL  
**Complexity:** HIGH  
**Estimated Time:** 5-6 hours

**Files to create:**
```
docker/whisperx/Dockerfile
docker/whisperx/whisperx.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir whisperx faster-whisper torch torchaudio
```

**Implementation:**
```python
# Pseudocode for whisperx.py
1. Load audio, VAD segments, diarization, initial prompt
2. Load WhisperX model (from config: large-v3, medium, etc.)
3. Transcribe with forced alignment
4. Apply speaker labels from diarization
5. Translate to English (task=translate)
6. Save word-level timestamps
```

**Input:** 
- `temp/audio/*.wav`
- `temp/vad/pyannote_segments.json`
- `temp/diarization/speakers.json`
- `temp/prompts/initial_prompt.txt`

**Output:** `temp/transcripts/whisperx.json`

---

### Container 8: Post-ASR NER

**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Estimated Time:** 3-4 hours

**Files to create:**
```
docker/post-ner/Dockerfile
docker/post-ner/post_ner.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir spacy transformers rapidfuzz
```

**Implementation:**
```python
# Pseudocode for post_ner.py
1. Load WhisperX transcripts
2. Load TMDB metadata and Pre-NER entities
3. Run NER on transcribed text
4. Correct entity spellings using TMDB data
5. Fix common ASR errors
6. Save corrected entities
```

**Input:** 
- `temp/transcripts/whisperx.json`
- `temp/metadata/tmdb_data.json`
- `temp/entities/pre_ner.json`

**Output:** `temp/entities/post_ner.json`, `temp/transcripts/whisperx_corrected.json`

---

### Container 9: Subtitle Generation

**Priority:** CRITICAL  
**Complexity:** MEDIUM  
**Estimated Time:** 3-4 hours

**Files to create:**
```
docker/subtitle-gen/Dockerfile
docker/subtitle-gen/subtitle_gen.py
```

**Dependencies:**
```dockerfile
RUN pip install --no-cache-dir pysrt
```

**Implementation:**
```python
# Pseudocode for subtitle_gen.py
1. Load corrected transcripts
2. Format subtitles according to config:
   - Max line length
   - Max lines per subtitle
   - Speaker label format
3. Generate SRT format
4. Apply timing adjustments
5. Save SRT file
```

**Input:** `temp/transcripts/whisperx_corrected.json`
**Output:** `temp/subtitles/movie.srt`

---

## 📋 Implementation Order (Recommended)

### Phase 1: Metadata Pipeline (Week 1)
1. ✅ demux (DONE)
2. **tmdb** - Implement TMDB fetcher
3. **pre-ner** - Implement Pre-ASR NER
4. Test: Can we build initial prompt?

### Phase 2: VAD & Diarization (Week 2)
5. **silero-vad** - Implement Silero VAD
6. **pyannote-vad** - Implement PyAnnote VAD
7. **diarization** - Implement speaker diarization
8. Test: Can we identify speech and speakers?

### Phase 3: Core Transcription (Week 3)
9. **whisperx** - Implement WhisperX ASR (most complex)
10. Test: Can we transcribe with speakers?

### Phase 4: Post-Processing (Week 4)
11. **post-ner** - Implement entity correction
12. **subtitle-gen** - Implement SRT generation
13. ✅ mux (DONE)
14. Test: Complete end-to-end pipeline

---

## 🧪 Testing Strategy

### Unit Testing (Per Container)
```bash
# Test individual container
docker-compose -f docker-compose.new.yml run --rm tmdb "Movie Title" "2020"

# Check output
cat temp/metadata/tmdb_data.json
```

### Integration Testing (Sequential)
```bash
# Test first 3 steps
python3 pipeline.py in/test.mp4
# Should complete: demux → tmdb → pre-ner

# Check logs
tail logs/orchestrator_*.log
```

### End-to-End Testing
```bash
# Full pipeline on short clip (5 min)
python3 pipeline.py in/short-clip.mp4

# Check final output
ls -lh out/*_with_subs.mp4
```

---

## 🎯 Success Criteria

### Per Container
- ✅ Container builds successfully
- ✅ Runs without errors
- ✅ Produces expected output format
- ✅ Logs to logs/ directory
- ✅ Reads config from .env
- ✅ Handles errors gracefully

### Complete Pipeline
- ✅ Passes preflight checks
- ✅ All 10 steps execute
- ✅ Generates valid SRT
- ✅ Embeds subtitles correctly
- ✅ Processes full-length movie
- ✅ All logs captured

---

## 📦 Deliverables Per Container

For each container, deliver:

1. **Dockerfile** - Extends base image, adds dependencies
2. **Python script** - Main processing logic
3. **README.md** - Container-specific docs
4. **Test inputs** - Sample data for testing
5. **Test outputs** - Expected results

---

## 🚀 Quick Start for Next Developer

```bash
# Clone repo
git clone <repo>
cd cp-whisperx-app

# Setup
./quick-start.sh

# Choose a container to implement (start with tmdb)
cd docker/tmdb

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM rajiup/cp-whisperx-app-base:latest
LABEL description="TMDB Metadata Fetch"
USER root
RUN pip install --no-cache-dir requests tmdbv3api
COPY docker/tmdb/tmdb.py /app/
USER appuser
ENTRYPOINT ["python", "tmdb.py"]
EOF

# Create Python script
nano tmdb.py
# (Follow pattern from demux.py)

# Test build
docker build -t test-tmdb -f Dockerfile ../..

# Test run
docker run --rm \
  -v $(pwd)/../../config:/app/config:ro \
  -v $(pwd)/../../temp:/app/temp \
  -v $(pwd)/../../logs:/app/logs \
  test-tmdb "Movie Title" "2020"

# Check output
cat ../../temp/metadata/tmdb_data.json
```

---

## 💡 Tips for Implementation

1. **Start with tmdb** - Simplest, no heavy dependencies
2. **Copy patterns from demux.py** - It's a complete template
3. **Test incrementally** - Build → Run → Check output → Iterate
4. **Use DEBUG logging** - `LOG_LEVEL=DEBUG` in config/.env
5. **Check existing scripts/** - Some logic already exists
6. **Follow the data flow** - Each container has clear input/output

---

## 🎉 Once Complete

When all containers are implemented:

```bash
# Build all images
./scripts/build-images.sh

# Push to registry
./scripts/push-images.sh

# Update documentation
# Add example outputs
# Create demo video

# Test on real movie
python3 pipeline.py in/full-movie.mp4

# Celebrate! 🎊
```

---

**Current Status:** Foundation 100% Complete  
**Remaining Work:** 8 container implementations  
**Estimated Total Time:** 25-35 hours  
**Recommended Team Size:** 2-3 developers  
**Timeline:** 3-4 weeks (part-time) or 1 week (full-time)
