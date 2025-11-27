# Hybrid Translation Quick Setup

## 🚀 Quick Start (5 minutes)

### 1. Install LLM Environment

```bash
./install-llm.sh
```

### 2. Get API Key

Choose one provider:

**Option A: Anthropic Claude (Recommended)**
1. Sign up: https://console.anthropic.com/
2. Get API key from Settings → API Keys
3. Cost: ~$0.50-2.00 per movie

**Option B: OpenAI GPT-4**
1. Sign up: https://platform.openai.com/
2. Get API key from API Keys section
3. Cost: ~$1.00-3.00 per movie

### 3. Configure API Key

Edit `config/secrets.json`:

```json
{
  "anthropic_api_key": "sk-ant-YOUR-KEY-HERE"
}
```

Or set environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-YOUR-KEY-HERE"
```

### 4. Test It

```bash
# Test without LLM (baseline)
python test_hybrid_translator.py

# Test with LLM (requires API key)
python test_hybrid_translator.py --use-llm
```

### 5. Use in Pipeline

Add to your job config or `.env`:

```bash
USE_HYBRID_TRANSLATION=true
LLM_PROVIDER=anthropic
USE_LLM_FOR_SONGS=true
```

Run your pipeline normally:
```bash
./run-pipeline.sh -j <job-id>
```

## 📊 What You Get

### Before (IndicTrans2 only)
```
Song: "तेरा मुझसे है पहले का नाता कोई"
→ "You have some previous connection with me"
```
❌ Literal, loses poetic quality

### After (Hybrid Translation)
```
Song: "तेरा मुझसे है पहले का नाता कोई"
→ "We share a bond from before we met"
```
✅ Natural, poetic, emotionally accurate

### Dialogue (unchanged)
```
"सॉरी, यह हमारे ग्रुप का बहुत स्पेशल गाना है"
→ "Sorry, this is our group's very special song"
```
✅ Still fast, accurate IndicTrans2

## 💰 Cost Breakdown

**Example Movie (2.5 hours):**
- Total segments: ~1,500
- Song segments: ~150 (10%)
- Dialogue segments: ~1,350 (90%)

**Translation costs:**
- IndicTrans2 (dialogue): **$0** (free, local GPU)
- LLM (songs only): **~$0.50-2.00**

**Total per movie: ~$0.50-2.00**

Compare to:
- Manual subtitling: $500-2,000
- Professional translation: $100-500

## ⚙️ Configuration Options

```bash
# Enable hybrid translation
USE_HYBRID_TRANSLATION=true

# LLM provider (anthropic or openai)
LLM_PROVIDER=anthropic

# Use LLM for songs (set false to use IndicTrans2 for everything)
USE_LLM_FOR_SONGS=true

# Lyrics detection sensitivity (0.0-1.0)
LYRICS_DETECTION_THRESHOLD=0.5

# Film context (auto-loaded if available)
FILM_TITLE="Jaane Tu Ya Jaane Na"
FILM_YEAR=2008
```

## 🎯 When to Use LLM

**Use LLM for:**
- ✅ Songs/poetry with rhyme schemes
- ✅ Creative/metaphorical language
- ✅ Emotional/romantic content
- ✅ Films with cultural nuances

**Use IndicTrans2 only for:**
- ✅ Documentary/factual content
- ✅ Technical dialogue
- ✅ Cost-sensitive projects
- ✅ Offline processing

## 🔧 Troubleshooting

### API Key Not Found

```bash
# Check if key is in secrets.json
cat config/secrets.json | grep anthropic

# Or set as environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
```

### LLM Not Available

System automatically falls back to IndicTrans2:
```
⚠ LLM client not available: API key not found
  Will fallback to IndicTrans2 for all translations
```

### Test First

Always test before running full movie:
```bash
python test_hybrid_translator.py --use-llm
```

## 📚 Documentation

Full documentation: `docs/HYBRID_TRANSLATION.md`

## 🆘 Support

Issues? Check:
1. API key configured correctly
2. LLM environment installed (`./install-llm.sh`)
3. Test script passes (`test_hybrid_translator.py --use-llm`)
4. Check logs in `out/*/logs/hybrid_translation.log`
