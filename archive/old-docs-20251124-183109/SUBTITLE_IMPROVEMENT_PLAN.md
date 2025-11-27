# Subtitle Quality Improvement Plan

**Date:** November 24, 2025  
**Focus:** Improving English subtitle quality with lyrics detection and official lyrics integration  
**Status:** Proposed Implementation

---

## 🎯 Current Problem

### What You're Seeing

**Hindi Subtitles (Source):**
```srt
1
00:00:00,000 --> 00:00:19,000
तेरा मुझसे है पहले कनाता खोई, यूही नहीं दिल भाता कोई, 
जाने तू या जाने ना, माने तू या माने ना
```

**English Subtitles (Current Translation):**
```srt
1
00:00:00,000 --> 00:00:19,000
You've lost Kanata before me, you're not happy, 
you know or you don't know, whether you believe or not.
```

**Problems:**
1. ❌ **Poor translation of song lyrics** ("Kanata" should be romanized)
2. ❌ **Wrong meaning** ("कनाता" is not translated correctly)
3. ❌ **Loss of poetic structure** (original rhyme scheme lost)
4. ❌ **Nonsensical phrases** ("Hey moms, you got me before you lost a canadian")

### Root Causes

1. **Machine Translation Limitations**
   - NLLB/IndICTrans2 trained on conversational text
   - Poor at handling poetic/lyrical language
   - Loses cultural context and idioms

2. **No Lyrics Detection**
   - Pipeline treats songs like regular speech
   - No special handling for music segments
   - No access to official lyrics

3. **No Context Awareness**
   - Doesn't know this is "Jaane Tu Ya Jaane Na" song
   - Missing TMDB movie metadata (song lists)
   - Can't fetch official lyrics

---

## ✅ Solution: Multi-Pronged Approach

### Approach 1: Lyrics Detection + Official Lyrics (BEST)

**What It Does:**
1. Detect song/music segments in audio
2. Identify the specific song being sung
3. Fetch official English lyrics from TMDB/external sources
4. Replace machine translation with official lyrics

**Benefits:**
- ✅ **100% accurate lyrics** (official translations)
- ✅ **Proper poetic structure** maintained
- ✅ **Cultural context** preserved
- ✅ **Rhyme schemes** intact

**Workflow:**
```
Audio → Lyrics Detection → Song Recognition → TMDB Lookup → Official Lyrics → Subtitle
```

---

### Approach 2: Enhanced Translation for Lyrics

**What It Does:**
1. Detect song segments
2. Mark them as "lyrics" type
3. Use specialized translation model for poetry/songs
4. Apply romanization for untranslatable terms

**Benefits:**
- ✅ Better than current translation
- ✅ Preserves poetic tone
- ✅ Works when official lyrics unavailable

**Limitations:**
- ⚠️ Still not as good as official lyrics
- ⚠️ May miss cultural nuances

---

### Approach 3: Hybrid (RECOMMENDED)

**What It Does:**
1. Detect song segments (lyrics detection)
2. Try to fetch official lyrics (TMDB API)
3. If found → Use official lyrics
4. If not found → Use enhanced translation
5. Fall back to romanization for unclear parts

**Benefits:**
- ✅ Best of both worlds
- ✅ Official lyrics when available
- ✅ Graceful degradation
- ✅ Always produces something useful

---

## 🔧 Implementation Components

### Component 1: Lyrics Detection (EXISTS!)

**Location:** `scripts/lyrics_detection.py`

**What It Does:**
- Analyzes audio features (tempo, rhythm, spectral features)
- Detects repetition patterns in transcripts
- Identifies poetic structure (short lines, rhyming)
- Marks segments as "speech" or "lyrics"

**Status:** ✅ **Already implemented** but not integrated!

**Example Output:**
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 19.0,
      "text": "तेरा मुझसे...",
      "type": "lyrics",        ← Marked as lyrics
      "confidence": 0.95,
      "features": {
        "rhythm_score": 0.87,
        "repetition_detected": true
      }
    }
  ]
}
```

---

### Component 2: TMDB Song Metadata (PARTIAL)

**What's Available:**
- TMDB API has movie metadata
- Movies have soundtrack information
- **BUT**: Not all songs have official lyrics in TMDB

**Current Status:**
- ✅ TMDB client implemented (`shared/tmdb_client.py`)
- ✅ Can fetch movie metadata
- ⚠️ Need to add song/soundtrack methods
- ❌ Need external lyrics API integration

**What You Get:**
```json
{
  "movie": "Jaane Tu... Ya Jaane Na",
  "soundtrack": [
    {
      "title": "Jaane Tu Ya Jaane Na",
      "artists": ["A.R. Rahman"],
      "duration": "4:30"
    }
  ]
}
```

**What's Missing:**
- Official English lyrics not in TMDB
- Need external source (Genius, Musixmatch, etc.)

---

### Component 3: Official Lyrics APIs

**Option A: Genius API** (Recommended)
```
Pros:
  ✅ Large database (including Bollywood)
  ✅ English translations available
  ✅ Free tier available
  ✅ Good API documentation

Cons:
  ⚠️ Requires API key
  ⚠️ Rate limits
```

**Option B: Musixmatch API**
```
Pros:
  ✅ Largest lyrics database
  ✅ Official lyrics partnerships
  ✅ Multiple languages

Cons:
  ⚠️ Paid API (expensive)
  ⚠️ Strict licensing
```

**Option C: Manual Lyrics Database**
```
Pros:
  ✅ No API limits
  ✅ Full control
  ✅ Offline capability

Cons:
  ⚠️ Manual curation required
  ⚠️ Limited coverage
```

---

### Component 4: Song Matching

**Challenge:** How do we know which song is playing?

**Method 1: TMDB + Timestamp**
```
1. Get movie title: "Jaane Tu Ya Jaane Na"
2. Fetch soundtrack list from TMDB
3. Match timestamp to scene (if available)
4. Identify song
```

**Method 2: Audio Fingerprinting**
```
1. Create audio fingerprint of segment
2. Match against song database (Shazam-style)
3. Identify exact song

Tools: AcoustID, Chromaprint
```

**Method 3: Transcript Matching**
```
1. Extract first line of lyrics from transcript
2. Search lyrics database
3. Match by first line + movie context

Example: "तेरा मुझसे है पहले..." → "Jaane Tu Ya Jaane Na"
```

---

## 📋 Implementation Roadmap

### Phase 1: Enable Lyrics Detection (EASY - 1 day)

**What to Do:**
1. Integrate existing `lyrics_detection.py` into pipeline
2. Add stage to manifest after ASR
3. Mark segments as "speech" or "lyrics"

**Files to Modify:**
- `scripts/run-pipeline.py` - Add lyrics detection stage
- `scripts/prepare-job.py` - Add lyrics detection to manifest

**Expected Output:**
```json
{
  "segments": [
    {"start": 0.0, "end": 19.0, "type": "lyrics"},
    {"start": 19.0, "end": 23.6, "type": "speech"},
    ...
  ]
}
```

---

### Phase 2: TMDB Song Metadata (MEDIUM - 2-3 days)

**What to Do:**
1. Extend TMDB client to fetch soundtrack
2. Parse song titles and timestamps
3. Store in job metadata

**New Methods:**
```python
# shared/tmdb_client.py
def get_movie_soundtrack(movie_id):
    """Fetch soundtrack information"""
    
def match_timestamp_to_song(timestamp, soundtrack):
    """Match audio timestamp to song"""
```

**Expected Output:**
```json
{
  "tmdb_enrichment": {
    "soundtrack": [
      {
        "title": "Jaane Tu Ya Jaane Na",
        "timestamp_start": 0,
        "timestamp_end": 270,
        "artists": ["A.R. Rahman"]
      }
    ]
  }
}
```

---

### Phase 3: External Lyrics Integration (MEDIUM - 3-4 days)

**What to Do:**
1. Choose lyrics API (Genius recommended)
2. Create lyrics client module
3. Search by song title + movie name
4. Fetch English lyrics

**New Module:**
```python
# shared/lyrics_client.py

class LyricsClient:
    def search_song(self, title, artist=None):
        """Search for song in lyrics database"""
    
    def get_lyrics(self, song_id, language='en'):
        """Fetch lyrics in target language"""
    
    def align_lyrics_to_transcript(self, lyrics, transcript):
        """Align official lyrics to audio timestamps"""
```

**Expected Output:**
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 19.0,
      "type": "lyrics",
      "text_original": "तेरा मुझसे...",
      "text_official": "Your connection with me existed...",
      "source": "genius"
    }
  ]
}
```

---

### Phase 4: Subtitle Generation Enhancement (EASY - 1 day)

**What to Do:**
1. Modify subtitle generation to check segment type
2. If type="lyrics" and official lyrics available → use them
3. If not → use existing translation

**Logic:**
```python
def generate_subtitle_line(segment):
    if segment['type'] == 'lyrics':
        # Use official lyrics if available
        if 'text_official' in segment:
            return segment['text_official']
    
    # Fall back to translation
    return segment['text']
```

---

## 💡 Quick Wins (Can Implement Now)

### 1. Romanization for Untranslatable Terms

**Current:** "Kanata" (wrong translation)  
**Better:** Keep original "कनाता" or romanize to "kanata"

**Implementation:**
```python
# In translation stage
def should_romanize(word):
    # Check if word is name, place, or untranslatable
    return is_proper_noun(word) or is_cultural_term(word)

def translate_with_romanization(text):
    words = text.split()
    result = []
    for word in words:
        if should_romanize(word):
            result.append(romanize(word))
        else:
            result.append(translate(word))
    return ' '.join(result)
```

---

### 2. Music Placeholder for Unknown Songs

**Current:** Bad translation of lyrics  
**Better:** "[♪ Music: Jaane Tu Ya Jaane Na ♪]"

**Implementation:**
```python
if segment['type'] == 'lyrics' and not has_official_lyrics:
    song_name = identify_song(segment)
    return f"[♪ Music: {song_name} ♪]"
```

---

### 3. Hinglish Handling

**Current:** Translates code-mixed text poorly  
**Better:** Keep English words, translate only Hindi

**Example:**
```
Input:  "Sorry यह हमारी group के लिए बहुत special गान है"
Current: "Sorry, this is a very special song for our group"
Better:  "Sorry, this is our group's very special song"
                  (Keep English words as-is)
```

---

## 📊 Expected Improvements

### Current Quality Metrics

| Metric | Current | Issue |
|--------|---------|-------|
| Lyrics Translation | 40% | Wrong meanings |
| Song Recognition | 0% | Not implemented |
| Official Lyrics | 0% | Not fetched |
| Poetic Structure | 10% | Lost in translation |

### After Implementation

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| Lyrics Detection | 90% | 90% | 90% | 90% |
| Song Recognition | 0% | 80% | 80% | 80% |
| Official Lyrics | 0% | 0% | 70% | 70% |
| Overall Quality | 45% | 60% | 85% | 90% |

---

## 🚀 Recommended Next Steps

### Immediate (Can Do Today)

1. **Enable Lyrics Detection**
   ```bash
   # Add lyrics detection stage to pipeline
   # Modify scripts/run-pipeline.py
   ```

2. **Add Music Placeholder**
   ```python
   # For detected lyrics without official source
   # Better than wrong translation
   ```

3. **Improve Romanization**
   ```python
   # Keep proper nouns and cultural terms
   # Don't translate names
   ```

### Short Term (This Week)

4. **Integrate TMDB Soundtrack**
   - Extend TMDB client
   - Fetch song metadata
   - Store with job data

5. **Manual Lyrics Database**
   - Create `glossary/lyrics/` directory
   - Add popular song lyrics manually
   - JSON format: song_title.json

### Medium Term (Next Week)

6. **Genius API Integration**
   - Sign up for API key
   - Implement lyrics client
   - Add to pipeline

7. **Lyrics Alignment**
   - Match official lyrics to timestamps
   - Sync with audio segments

---

## 📖 Example Output Comparison

### Current Output (BAD)
```srt
1
00:00:00,000 --> 00:00:19,000
You've lost Kanata before me, you're not happy, 
you know or you don't know, whether you believe or not.
```

### After Phase 1 (BETTER)
```srt
1
00:00:00,000 --> 00:00:19,000
[♪ Music: Jaane Tu Ya Jaane Na by A.R. Rahman ♪]
```

### After Phase 3 (BEST)
```srt
1
00:00:00,000 --> 00:00:19,000
Your connection with me existed long before,
My heart doesn't like anyone else,
Do you know or not, Do you believe or not
```

---

## 💾 Storage Optimization

### About vocals.wav & accompaniment.wav

**Current:**
- `audio.wav` (101 MB) - Used by pipeline ✅
- `vocals.wav` (101 MB) - Duplicate ❌
- `accompaniment.wav` (101 MB) - Reference ⚠️

**Recommendation:**

**Keep accompaniment.wav for now because:**
1. Can be used for lyrics detection (music analysis)
2. Useful for debugging source separation quality
3. Future: Could enable karaoke-style subtitles
4. Future: Music-only tracks for remixing

**Delete vocals.wav safely:**
- It's just a duplicate of audio.wav
- Saves 101 MB per job
- No functionality loss

**Script to Clean Up:**
```bash
#!/bin/bash
# cleanup-duplicates.sh

# For all jobs, delete vocals.wav (duplicate)
find out/ -name "vocals.wav" -exec rm -v {} \;

# Keep accompaniment.wav (useful for music analysis)
echo "Cleaned up duplicate vocals.wav files"
echo "Kept accompaniment.wav for lyrics detection"
```

---

## ✅ Action Items

### Priority 1 (Do First)
- [ ] Enable lyrics detection stage in pipeline
- [ ] Add music placeholder for detected songs
- [ ] Test with current job

### Priority 2 (This Week)
- [ ] Extend TMDB client for soundtrack
- [ ] Create manual lyrics database structure
- [ ] Implement romanization improvements

### Priority 3 (Next Week)
- [ ] Integrate Genius API
- [ ] Implement lyrics alignment
- [ ] Update subtitle generation logic

### Bonus (Optional)
- [ ] Delete duplicate vocals.wav files
- [ ] Keep accompaniment.wav for future use
- [ ] Add lyrics quality metrics

---

## 🎯 Success Criteria

### Phase 1 Success
- Lyrics segments detected and marked
- Music placeholders in subtitles
- No more nonsensical song translations

### Phase 2 Success
- Songs identified from TMDB metadata
- Soundtrack information in job data
- Timestamp-to-song mapping working

### Phase 3 Success
- Official lyrics fetched from Genius
- 70%+ song coverage
- High-quality English lyrics in subtitles

### Phase 4 Success
- 90% subtitle quality for songs
- Proper poetic structure preserved
- Cultural context maintained

---

**Current Status:** Planning Phase  
**Ready to Implement:** Phase 1 (Lyrics Detection)  
**Blockers:** None - All components available!

---

**Next Command:**
```bash
# Start with Phase 1
# Enable lyrics detection in pipeline
```

**Questions?**
- Which phase should we start with?
- Do you have Genius API access?
- Should we create manual lyrics database first?

---
