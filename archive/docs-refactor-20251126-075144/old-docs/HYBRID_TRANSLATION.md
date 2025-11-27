# Hybrid Translation System

**Intelligent translation combining IndicTrans2 for dialogue + LLM for songs/poetry**

## Overview

The Hybrid Translation system automatically routes different types of content to the most appropriate translation method:

- **Dialogue** → IndicTrans2 (fast, accurate, local)
- **Songs/Lyrics** → LLM with film context (creative, culturally aware)
- **Named Entities** → Preserved across both methods

## Architecture

```
Transcript (Hindi/Indic)
         ↓
   Lyrics Detection
    /           \
Dialogue      Songs/Poetry
   ↓              ↓
IndicTrans2     LLM + Context
   ↓              ↓
    \           /
     Translated
     Segments
```

## Installation

### 1. Install LLM Environment

```bash
./install-llm.sh
```

This installs:
- Anthropic Claude SDK
- OpenAI GPT SDK
- Supporting libraries

### 2. Configure API Keys

Add to `config/secrets.json`:

```json
{
  "anthropic_api_key": "sk-ant-...",
  "openai_api_key": "sk-..."
}
```

**Get API Keys:**
- **Anthropic Claude**: https://console.anthropic.com/
- **OpenAI GPT**: https://platform.openai.com/api-keys

### 3. Enable in Pipeline

Add to your `.env` or job config:

```bash
# Enable hybrid translation
USE_HYBRID_TRANSLATION=true

# LLM provider (anthropic or openai)
LLM_PROVIDER=anthropic

# Use LLM for songs (true/false)
USE_LLM_FOR_SONGS=true
```

## How It Works

### Lyrics Detection

The system uses `lyrics_detection.py` to identify song segments:

1. **Audio features** - tempo, rhythm, spectral patterns
2. **Repetition detection** - repeated phrases (choruses)
3. **Pattern matching** - short lines, poetic structure

### Translation Routing

```python
if segment.is_song and USE_LLM_FOR_SONGS:
    # Use LLM with film context
    translation = llm_translate(text, film_context)
else:
    # Use IndicTrans2
    translation = indictrans2_translate(text)
```

### Context-Aware LLM Prompts

For songs, the LLM receives:

```
Translate this Hindi song lyric to natural, poetic English.

Guidelines:
- Preserve poetic rhythm and emotion
- Use natural, contemporary language
- Maintain rhyme scheme if possible

Film Context:
Title: Jaane Tu Ya Jaane Na (2008)
Setting: Mumbai, college friends
Tone: Casual, youth-oriented, romantic

Original (Hindi):
तेरा मुझसे है पहले का नाता कोई
यूं ही नहीं दिल लुभाता कोई

Natural English translation:
```

## Benefits

### For Dialogue (IndicTrans2)
✅ Fast (10-100x faster than LLM)  
✅ Accurate for conversational text  
✅ Works offline (no API costs)  
✅ Consistent terminology  

### For Songs (LLM)
✅ Poetic, natural translations  
✅ Context-aware (understands film setting)  
✅ Maintains emotional tone  
✅ Creative rhyme/rhythm preservation  

## Cost Estimation

### IndicTrans2 (Dialogue)
- **Cost**: Free (local GPU/CPU)
- **Speed**: ~100 segments/sec
- **Quality**: 85-90% for dialogue

### LLM (Songs Only)
- **Cost**: ~$0.01-0.05 per song (10-20 segments)
- **Speed**: ~1-2 segments/sec
- **Quality**: 90-95% for creative content

**Example Movie (2.5 hours):**
- Total segments: ~1,500
- Song segments: ~150 (10%)
- Dialogue segments: ~1,350 (90%)

**Cost breakdown:**
- IndicTrans2: $0 (free)
- LLM: ~$0.50-2.00 (songs only)
- **Total**: ~$0.50-2.00 per movie

## Configuration Options

### Environment Variables

```bash
# Translation method
USE_HYBRID_TRANSLATION=true  # Enable hybrid mode
USE_LLM_FOR_SONGS=true       # Use LLM for songs

# LLM provider
LLM_PROVIDER=anthropic       # anthropic or openai

# Lyrics detection
LYRICS_DETECTION_ENABLED=true
LYRICS_DETECTION_THRESHOLD=0.5
LYRICS_MIN_DURATION=30.0

# Film context
FILM_TITLE="Jaane Tu Ya Jaane Na"
FILM_YEAR=2008
```

### Glossary Integration

The hybrid translator can use the glossary for:
- Location names (Mumbai, Cuffe Parade, Churchgate)
- Character nicknames (Rats, Meow, Jiggy)
- Cultural terms (yaar → dude, bhai → bro)

## Examples

### Input Segment (Song)

```json
{
  "start": 0.0,
  "end": 19.0,
  "text": "तेरा मुझसे है पहले का नाता कोई, यूं ही नहीं दिल लुभाता कोई",
  "is_lyric": true
}
```

### Translation Methods Compared

**IndicTrans2 (literal):**
> "You have some previous connection with me, not just anyone charms the heart like this"

**LLM with context:**
> "We share a bond from before we met, you've captured my heart like no one else could"

### Input Segment (Dialogue)

```json
{
  "start": 23.64,
  "end": 27.5,
  "text": "सच, इसलिए कप पिरीट से चर्च गेट तक गाते हुए आए थे",
  "is_lyric": false
}
```

**Translation (IndicTrans2 + Glossary):**
> "True, that's why we came singing from Cuffe Parade to Churchgate"

## Pipeline Integration

### Stage Order

1. **Source Separation** (if enabled)
2. **WhisperX Transcription**
3. **Lyrics Detection** ← identifies songs
4. **Hybrid Translation** ← NEW STAGE
5. **Glossary Application**
6. **Subtitle Generation**

### Stage Input/Output

**Input:** `segments.json` from lyrics_detection stage
```json
{
  "segments": [
    {
      "text": "तेरा मुझसे है पहले का नाता कोई",
      "is_lyric": true,
      "start": 0.0,
      "end": 19.0
    }
  ]
}
```

**Output:** `translated_segments.json`
```json
{
  "segments": [
    {
      "text": "We share a bond from before we met",
      "translation_method": "llm",
      "translation_confidence": 0.95,
      "is_lyric": true,
      "start": 0.0,
      "end": 19.0
    }
  ],
  "translation_stats": {
    "total_segments": 1500,
    "dialogue_segments": 1350,
    "song_segments": 150,
    "indictrans2_used": 1350,
    "llm_used": 150
  }
}
```

## Troubleshooting

### LLM API Errors

**Error:** `Anthropic API key not found`

**Solution:**
```bash
# Add to config/secrets.json
{
  "anthropic_api_key": "sk-ant-..."
}

# Or set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Fallback Behavior

If LLM fails (API error, rate limit), the system automatically falls back to IndicTrans2:

```
⚠ LLM translation failed: Rate limit exceeded
  Falling back to IndicTrans2 for segment
```

### Testing Without API Keys

```bash
# Disable LLM (use IndicTrans2 for everything)
USE_LLM_FOR_SONGS=false
```

## Performance

### Speed Comparison

| Method | Segments/sec | GPU | API Cost |
|--------|--------------|-----|----------|
| IndicTrans2 | 100-200 | Yes | $0 |
| LLM (Claude) | 1-2 | No | ~$0.003/segment |
| LLM (GPT-4) | 1-2 | No | ~$0.005/segment |

### Quality Comparison

| Content Type | IndicTrans2 | LLM |
|--------------|-------------|-----|
| Dialogue | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Songs/Poetry | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Idioms | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Technical | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Future Enhancements

- [ ] GPT-4o/Claude Opus for higher quality
- [ ] Batch processing for cost optimization
- [ ] Caching of similar song translations
- [ ] Multi-language LLM support (beyond English)
- [ ] Fine-tuned models for Bollywood context
- [ ] User feedback integration for quality improvement

## Credits

- **IndicTrans2**: AI4Bharat (IIT Madras)
- **Anthropic Claude**: Context-aware creative translation
- **Lyrics Detection**: Audio feature + pattern analysis

## License

MIT License (same as cp-whisperx-app)
