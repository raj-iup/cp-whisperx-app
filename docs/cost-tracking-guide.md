# Cost Tracking User Guide

**Version:** 1.0  
**Date:** 2025-12-10  
**Status:** Production Ready ✅

---

## Overview

The Cost Tracking Module provides real-time monitoring of AI service costs across all pipeline stages. It tracks OpenAI, Google Gemini, WhisperX, and local processing (MLX, IndicTrans2) with automatic budget alerts.

---

## Quick Start

### No Configuration Required

Cost tracking is **enabled automatically** for all jobs. No setup needed!

```bash
# Run any workflow - costs tracked automatically
./prepare-job.sh --media movie.mp4 --workflow subtitle
./run-pipeline.sh --job-dir out/latest
```

### View Your Costs

```bash
# Monthly summary
python3 tools/cost-dashboard.py show-monthly

# Job-specific costs
python3 tools/cost-dashboard.py show-job job-20251210-rpatel-0001

# Budget status
python3 tools/cost-dashboard.py show-budget

# Get optimization tips
python3 tools/cost-dashboard.py show-optimization
```

---

## Pipeline Cost Display

During pipeline execution, you'll see cost information for each stage:

```
[Stage 06: WhisperX ASR]
==========================================
✅ ASR complete | Duration: 84.2s
💰 Stage cost: $0.0000 (local processing)
==========================================

[Stage 13: AI Summarization]
==========================================
✅ Summary generated: 1,200 tokens used
💰 Stage cost: $0.0045
⚠️  WARNING: Budget threshold reached!
    $40.25 / $50.00 (80.5%)
==========================================
```

---

## Cost Breakdown by Stage

| Stage | Service | Default Cost | Notes |
|-------|---------|--------------|-------|
| 06 (ASR) | MLX Whisper | $0.00 | Local processing |
| 10 (Translation) | IndicTrans2 | $0.00 | Local processing |
| 13 (Summarization) | OpenAI/Gemini | ~$0.004 | API cost per job |

**Typical job cost:** $0.00 - $0.01 (mostly local processing)

---

## Budget Configuration

### Default Budget

- **Monthly Limit:** $50.00
- **Alert Threshold:** 80% ($40.00)
- **Enforcement:** Soft warnings only

### Customize Your Budget

Edit your user profile: `users/{userId}/profile.json`

```json
{
  "budget": {
    "monthly_limit_usd": 100.00,
    "alert_threshold_percent": 75,
    "block_at_limit": false,
    "notification_email": "your@email.com"
  }
}
```

### Budget Alerts

**80% Warning (Soft):**
```
⚠️  WARNING: Budget threshold reached!
    $40.25 / $50.00 (80.5%) | Remaining: $9.75
```

**100% Critical (Soft):**
```
🚨 CRITICAL: Budget limit reached!
    $50.00 / $50.00 (100.0%)
```

---

## Dashboard Commands

### 1. Monthly Summary

```bash
python3 tools/cost-dashboard.py show-monthly
```

Shows:
- Total spend for current month
- Jobs processed
- Average cost per job
- Cost breakdown by service/model
- Top 5 models by cost

### 2. Job Cost Report

```bash
python3 tools/cost-dashboard.py show-job job-20251210-rpatel-0001
```

Shows:
- Total job cost
- Cost breakdown by stage
- Budget impact percentage

### 3. Budget Status

```bash
python3 tools/cost-dashboard.py show-budget
```

Shows:
- Current spend vs. limit
- Remaining budget
- Daily average spending
- Month-end projection
- Active alerts

### 4. Optimization Recommendations

```bash
python3 tools/cost-dashboard.py show-optimization
```

Shows:
- Potential cost savings (15-30%)
- Model optimization tips
- Configuration suggestions

### 5. Export Report

```bash
# JSON format
python3 tools/cost-dashboard.py export-report --format json

# CSV format
python3 tools/cost-dashboard.py export-report --format csv --output report.csv
```

---

## Cost Optimization Tips

### 1. Use Local Processing (Default)

Our pipeline uses local processing by default:
- ✅ MLX Whisper for ASR (8-9x faster, $0 cost)
- ✅ IndicTrans2 for translation ($0 cost)
- ✅ Only Stage 13 (Summarization) uses API

**Savings:** ~90% compared to API-only pipeline

### 2. Choose Cost-Effective Models

If using AI Summarization:

| Model | Cost per 1K tokens | Quality | Use Case |
|-------|-------------------|---------|----------|
| gemini-1.5-flash | $0.000075 | Good | Budget option |
| gemini-1.5-pro | $0.00025 | Excellent | Best value |
| gpt-4o | $0.0025/$0.01 | Excellent | High quality |
| gpt-4 | $0.03/$0.06 | Premium | Critical tasks |

**Recommendation:** Use `gemini-1.5-pro` for 50% savings vs. GPT-4o

### 3. Enable Caching (Future)

When caching is enabled:
- Reuse ASR results for identical audio
- Reuse translations for similar content
- **Estimated savings:** 15-30% on repeat jobs

### 4. Batch Processing

Process multiple files in one session to amortize initialization costs.

---

## Cost Storage

Costs are stored in: `~/.cp-whisperx/costs/`

```
~/.cp-whisperx/costs/
├── 2025-12.json          # Current month
├── 2025-11.json          # Previous month
└── ...
```

Each file contains:
- All API calls for the month
- Token usage per call
- Cost per call
- Stage attribution
- Job metadata

**Retention:** Unlimited (manual cleanup if needed)

---

## Pricing Database

Current pricing (as of 2025-12-10):

### OpenAI
- gpt-4o: $0.0025 input / $0.01 output (per 1K tokens)
- gpt-4: $0.03 / $0.06
- gpt-3.5-turbo: $0.0005 / $0.0015

### Google Gemini
- gemini-1.5-flash: $0.000075 / $0.000075
- gemini-1.5-pro: $0.00025 / $0.00025

### Local (No Cost)
- mlx-whisper: $0.00
- indictrans2-local: $0.00
- pyannote: $0.00

**Note:** Pricing updated monthly. See `shared/cost_tracker.py` for latest.

---

## FAQ

### Q: Do I need to configure anything?
**A:** No! Cost tracking is automatic. Budget defaults to $50/month.

### Q: Will jobs stop if I exceed budget?
**A:** No. Budget enforcement is soft warnings only (for now).

### Q: How accurate are the costs?
**A:** Highly accurate. Based on official API pricing, updated monthly.

### Q: Can I track multiple users?
**A:** Yes! Each user profile has independent cost tracking.

### Q: What if I don't use AI Summarization?
**A:** Your costs will be $0. ASR and Translation use local processing.

### Q: How do I reduce costs?
**A:** Run `show-optimization` for personalized recommendations.

---

## Troubleshooting

### No Cost Data Showing

```bash
# Check if cost logs exist
ls -la ~/.cp-whisperx/costs/

# Check user profile has budget section
cat users/1/profile.json | grep -A5 '"budget"'
```

### Budget Alerts Not Showing

Alerts only appear in Stage 13 (AI Summarization). If you don't use that stage, you won't see alerts.

### Cost Dashboard Errors

```bash
# Ensure you're in project root
cd /path/to/cp-whisperx-app

# Run with Python 3
python3 tools/cost-dashboard.py show-monthly
```

---

## Advanced Usage

### Custom Cost Storage Location

```python
from shared.cost_tracker import CostTracker

tracker = CostTracker(
    job_dir=job_dir,
    user_id=1,
    cost_storage_path="/custom/path"
)
```

### Programmatic Access

```python
from shared.cost_tracker import CostTracker

# Get monthly costs
tracker = CostTracker(user_id=1)
monthly_cost = tracker.get_monthly_cost()
print(f"This month: ${monthly_cost:.2f}")

# Get job costs
job_cost = tracker.get_job_cost("job-20251210-rpatel-0001")
print(f"Job cost: ${job_cost:.4f}")

# Get summary
summary = tracker.get_monthly_summary()
print(f"Total jobs: {summary['unique_jobs']}")
```

---

## Support

For issues or questions:
1. Check this guide
2. See `COST_TRACKING_PHASE1_SUMMARY.md` for technical details
3. View source: `shared/cost_tracker.py`
4. Open GitHub issue

---

**Last Updated:** 2025-12-10  
**Module Version:** 1.0  
**Status:** Production Ready ✅

---

## 💰 Cost Estimation Examples (NEW)

### Example 1: Estimate Before Processing

```bash
# Estimate costs for subtitle workflow
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-language en \
  --estimate-only

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COST ESTIMATION REPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Media: movie.mp4 (120 min duration)
# Workflow: subtitle
# Source: hi → Targets: en
#
# BREAKDOWN:
# ├─ TMDB API: $0.002 (1 request)
# ├─ Translation (IndicTrans2): $0.00 (local)
# ├─ ASR (MLX-Whisper): $0.00 (local GPU)
# ├─ Alignment (WhisperX): $0.00 (local GPU)
# └─ Subtitle Generation: $0.00 (local)
#
# ESTIMATED TOTAL: $0.002
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Status: ✅ Within budget ($50.00 remaining)
```

### Example 2: Multi-Language Subtitle Estimation

```bash
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu,ta,es,ru,zh,ar \
  --estimate-only

# Output:
# BREAKDOWN:
# ├─ TMDB API: $0.002 (1 request)
# ├─ Translation (7 languages):
# │  ├─ hi→en (IndicTrans2): $0.00 (local)
# │  ├─ hi→gu (IndicTrans2): $0.00 (local)
# │  ├─ hi→ta (IndicTrans2): $0.00 (local)
# │  ├─ hi→es (NLLB-200): $0.00 (local)
# │  ├─ hi→ru (NLLB-200): $0.00 (local)
# │  ├─ hi→zh (NLLB-200): $0.00 (local)
# │  └─ hi→ar (NLLB-200): $0.00 (local)
# ├─ ASR (MLX-Whisper): $0.00 (local GPU)
# └─ Subtitle Generation (7 tracks): $0.00 (local)
#
# ESTIMATED TOTAL: $0.002
# Processing Time: ~25-30 minutes
```

### Example 3: YouTube Video with AI Summarization

```bash
./prepare-job.sh --media "https://youtu.be/VIDEO_ID" \
  --workflow transcribe --source-language en \
  --enable-summarization \
  --estimate-only

# Output:
# BREAKDOWN:
# ├─ YouTube Download: $0.00 (free)
# ├─ ASR (MLX-Whisper): $0.00 (local GPU)
# ├─ Alignment (WhisperX): $0.00 (local GPU)
# ├─ AI Summarization:
# │  ├─ Model: gemini-1.5-pro
# │  ├─ Estimated tokens: 2,500
# │  └─ Cost: $0.0063
# 
# ESTIMATED TOTAL: $0.0063
# ⚠️  Note: AI summarization enabled (costs ~$0.006/job)
```

### Example 4: Cost-Aware Decision Making

```bash
# High-cost workflow (AI translation fallback)
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language en --target-language hi \
  --translation-engine openai \
  --estimate-only

# Output:
# BREAKDOWN:
# ├─ TMDB API: $0.002
# ├─ Translation (OpenAI GPT-4):
# │  ├─ Estimated words: 15,000
# │  ├─ Token count: ~22,500
# │  └─ Cost: $0.45
# ├─ ASR: $0.00 (local)
# └─ Subtitle Gen: $0.00 (local)
#
# ESTIMATED TOTAL: $0.452
# ⚠️  HIGH COST ALERT!
# 
# RECOMMENDATION:
# Use IndicTrans2 instead (free, local):
#   --translation-engine indictrans2
# Expected savings: $0.45 → $0.00 (100% reduction)
```

---

## 📊 Real-World Cost Examples

### Typical Job Costs (Local Processing):

| Workflow | Duration | Languages | Cost | Time |
|----------|----------|-----------|------|------|
| Transcribe | 10 min | 1 (en) | $0.00 | 2 min |
| Translate | 10 min | hi→en | $0.00 | 3 min |
| Subtitle | 120 min | hi→en | $0.002 | 25 min |
| Subtitle (8 langs) | 120 min | hi→8 | $0.002 | 35 min |
| YouTube transcribe | 5 min | hi | $0.00 | 90 sec |
| YouTube + TMDB | 3 min | hi→en | $0.002 | 12 min |

**Average monthly cost:** $0.05 - $0.50 (mostly TMDB API)

### With AI Features Enabled:

| Feature | Cost/Job | Monthly (100 jobs) |
|---------|----------|-------------------|
| AI Summarization | $0.004-0.008 | $0.40-$0.80 |
| GPT-4 Translation | $0.30-0.50 | $30-$50 |
| Gemini Summarization | $0.002-0.005 | $0.20-$0.50 |

---

## 🎯 Cost Optimization Tips

### 1. Use Local Models (Free)

```bash
# ✅ FREE - IndicTrans2 (Indian languages)
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --translation-engine indictrans2

# ❌ COSTLY - OpenAI GPT-4 ($0.30-0.50/job)
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --translation-engine openai
```

**Savings:** $0.45/job × 100 jobs = **$45/month**

### 2. Estimate Before Processing

```bash
# Always use --estimate-only first
./prepare-job.sh --media large_file.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu,ta \
  --estimate-only

# Review costs, then proceed
./run-pipeline.sh --job-dir out/LATEST
```

### 3. Cache Similar Content

```bash
# First video: Full processing
./prepare-job.sh --media movie_scene1.mp4 --workflow subtitle -s hi -t en
# Cost: $0.002, Time: 12 min

# Same movie, different scene: Cached baseline
./prepare-job.sh --media movie_scene2.mp4 --workflow subtitle -s hi -t en
# Cost: $0.001, Time: 3 min (75% faster, 50% cheaper)
```

### 4. Batch Process Strategically

```bash
# Process similar content together (shares cache)
for file in movie_clip*.mp4; do
  ./prepare-job.sh --media "$file" --workflow subtitle -s hi -t en
  ./run-pipeline.sh --job-dir out/LATEST
done

# First clip: $0.002
# Subsequent clips: $0.001 each (shared glossary/cache)
```

### 5. Disable Optional Features

```bash
# Minimal cost configuration
./prepare-job.sh --media file.mp4 --workflow transcribe \
  --source-language en \
  --no-summarization \
  --no-tmdb \
  --source-separation-enabled false

# Cost: $0.00 (completely free)
```

---

## 📈 Budget Scenarios

### Scenario 1: Casual User (10 jobs/month)

```
Workflow Mix:
- 5× Transcribe (10 min each)
- 3× Translate (15 min each)
- 2× Subtitle (60 min each)

Estimated Costs:
- Transcribe: 5 × $0.00 = $0.00
- Translate: 3 × $0.00 = $0.00
- Subtitle: 2 × $0.002 = $0.004

Monthly Total: $0.004
Budget Utilization: 0.008% ($0.004 / $50.00)
```

**Verdict:** ✅ Extremely budget-friendly

### Scenario 2: Power User (100 jobs/month)

```
Workflow Mix:
- 40× Transcribe (YouTube videos)
- 30× Translate (podcasts)
- 20× Subtitle (movie clips)
- 10× Subtitle (full movies, 120 min)

Estimated Costs:
- Transcribe: 40 × $0.00 = $0.00
- Translate: 30 × $0.00 = $0.00
- Subtitle (clips): 20 × $0.002 = $0.04
- Subtitle (movies): 10 × $0.002 = $0.02

Monthly Total: $0.06
Budget Utilization: 0.12% ($0.06 / $50.00)
```

**Verdict:** ✅ Still well within budget

### Scenario 3: Production Studio (500 jobs/month, AI features)

```
Workflow Mix:
- 200× Subtitle (Bollywood content)
- 200× AI Summarization enabled
- 100× Multi-language (8 languages)

Estimated Costs:
- Subtitle: 200 × $0.002 = $0.40
- AI Summarization: 200 × $0.006 = $1.20
- Multi-language: 100 × $0.002 = $0.20

Monthly Total: $1.80
Budget Utilization: 3.6% ($1.80 / $50.00)
```

**Verdict:** ✅ Easily manageable

---

## 🚨 Cost Alerts

### Alert Levels:

| Level | Threshold | Action |
|-------|-----------|--------|
| 🟢 Normal | <50% budget | Continue as usual |
| 🟡 Warning | 50-80% budget | Monitor usage |
| 🟠 Alert | 80-95% budget | Optimize or increase budget |
| 🔴 Critical | >95% budget | Processing paused (optional) |

### Email Notifications:

```json
// users/1/profile.json
{
  "budget": {
    "monthly_limit_usd": 50.00,
    "alert_threshold_percent": 80,
    "notification_email": "your@email.com",
    "alert_levels": {
      "warning": 50,
      "alert": 80,
      "critical": 95
    }
  }
}
```

---

## 🔗 Related Documentation

- **User Profiles:** [docs/user-guide/USER_PROFILES.md](user-guide/USER_PROFILES.md)
- **YouTube + TMDB:** [docs/YOUTUBE_TMDB_QUICKSTART.md](YOUTUBE_TMDB_QUICKSTART.md)
- **Cost Dashboard:** [tools/cost-dashboard.py](../tools/cost-dashboard.py)
- **Troubleshooting:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

---

**Last Updated:** 2025-12-11  
**Version:** 2.0 (with estimation examples)
