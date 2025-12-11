# Product Requirements Document: Cost Tracking & Optimization

**PRD ID:** PRD-2025-12-10-04-cost-tracking  
**Related BRD:** [BRD-2025-12-10-04-cost-tracking](../brd/BRD-2025-12-10-04-cost-tracking.md)  
**Status:** Draft  
**Owner:** Product Manager  
**Created:** 2025-12-10

---

## I. Introduction

### Purpose

Define product requirements for comprehensive cost tracking and optimization system across all AI services in cp-whisperx-app.

**Business Context** (from BRD):
- Track $8-17/month typical usage across transcription, translation, summarization
- Enable 15-30% cost reduction through optimization
- Foundation for Phase 6 ML features

### Scope

**In Scope:**
- Real-time cost tracking for all AI APIs
- Budget management with alerts
- Optimization recommendations
- Historical trend analysis
- ROI reporting

**Out of Scope:**
- Payment processing (not a billing system)
- Multi-currency support (USD only)
- Cost allocation across teams (single-user focus)

---

## II. User Personas & Stories

### Persona 1: Rachel the Researcher

**Demographics:**
- Age: 32, Location: Boston
- Role: PhD researcher
- Budget: $50/month for transcription

**Goals:**
- Stay within research grant budget
- Know costs before processing
- Optimize for cost efficiency

**Pain Points:**
- Cannot predict monthly costs
- No warning before budget exceeded
- Don't know which operations are expensive

**User Stories:**

**US-1.1: View Job Cost Estimate (MUST HAVE)**
> "As a researcher, I want to see estimated cost before starting a job, so that I can decide if it fits my budget."

**Acceptance Criteria:**
- ✅ Show cost estimate in prepare-job output
- ✅ Breakdown by stage (ASR, translation, summarization)
- ✅ Display total estimated cost
- ✅ Update estimate if parameters change

**US-1.2: Track Real-Time Costs (MUST HAVE)**
> "As a researcher, I want to see costs accumulate during processing, so that I know my spend in real-time."

**Acceptance Criteria:**
- ✅ Display current job cost in pipeline logs
- ✅ Show cumulative cost per stage
- ✅ Update cost every 30 seconds
- ✅ Final cost in job summary

**US-1.3: Stay Within Budget (MUST HAVE)**
> "As a researcher, I want to set a monthly budget and get alerts, so that I don't overspend."

**Acceptance Criteria:**
- ✅ Configure monthly budget in user profile
- ✅ Alert at 80% budget usage
- ✅ Critical alert at 100% usage
- ✅ Optional: Block jobs at budget limit

---

### Persona 2: Sam the Student

**Demographics:**
- Age: 21, Location: Mumbai
- Role: Computer Science student
- Budget: $10/month (limited funds)

**Goals:**
- Transcribe lectures affordably
- Use cheapest models that work
- Maximize value per dollar

**Pain Points:**
- Budget is very tight
- Doesn't know which models are cheaper
- Cannot afford premium features

**User Stories:**

**US-2.1: Get Cost Optimization Tips (SHOULD HAVE)**
> "As a student, I want suggestions to reduce costs, so that I can process more content with my limited budget."

**Acceptance Criteria:**
- ✅ Suggest cheaper models for simple tasks
- ✅ Recommend batch processing for efficiency
- ✅ Identify expensive features to disable
- ✅ Quantify potential savings ($ and %)

**US-2.2: Compare Model Costs (SHOULD HAVE)**
> "As a student, I want to compare costs of different models, so that I can choose the most affordable option."

**Acceptance Criteria:**
- ✅ Show cost per model in configuration guide
- ✅ Display cost comparison in job estimate
- ✅ Highlight cheapest option
- ✅ Show quality vs. cost tradeoff

**US-2.3: View Monthly Spending (MUST HAVE)**
> "As a student, I want to see my monthly spending breakdown, so that I know where my money goes."

**Acceptance Criteria:**
- ✅ Monthly cost report by model
- ✅ Cost per workflow (transcribe, translate, subtitle)
- ✅ Cost trends (daily chart)
- ✅ Projected month-end cost

---

### Persona 3: Chris the Content Creator

**Demographics:**
- Age: 28, Location: London
- Role: YouTube creator
- Budget: $100/month (business expense)

**Goals:**
- Track costs for tax purposes
- Optimize ROI (quality per dollar)
- Scale production affordably

**Pain Points:**
- Need cost reports for accounting
- Cannot measure cost-effectiveness
- Don't know if quality improvements worth cost

**User Stories:**

**US-3.1: Export Cost Reports (SHOULD HAVE)**
> "As a content creator, I want to export monthly cost reports, so that I can submit them for tax purposes."

**Acceptance Criteria:**
- ✅ Export monthly report as JSON
- ✅ Export monthly report as CSV
- ✅ Include all jobs with timestamps
- ✅ Include breakdown by cost category

**US-3.2: Measure ROI (NICE TO HAVE)**
> "As a content creator, I want to see cost vs. quality metrics, so that I can justify premium features."

**Acceptance Criteria:**
- ✅ Display cost per job with quality score
- ✅ Show quality improvement over baseline
- ✅ Calculate cost per quality point
- ✅ Highlight ROI of features

**US-3.3: Forecast Monthly Costs (SHOULD HAVE)**
> "As a content creator, I want to see projected monthly costs, so that I can plan my budget."

**Acceptance Criteria:**
- ✅ Project month-end cost based on trends
- ✅ Show days until budget exhausted
- ✅ Alert if on track to exceed budget
- ✅ Suggest pacing to stay in budget

---

## III. Functional Requirements

### FR-1: Cost Tracking Engine (MUST HAVE)

**Description:** Track costs for all AI API calls in real-time

**Components:**
1. **Cost Calculator:**
   - Token counting (input + output)
   - Rate lookup (from model registry)
   - Cost computation (tokens × rate)

2. **Usage Logger:**
   - Record every AI API call
   - Store: timestamp, model, tokens, cost, job_id
   - Append to monthly log file

3. **Cost Aggregator:**
   - Real-time totals (per job, per day, per month)
   - In-memory cache for fast lookups
   - Periodic sync to disk

**Interfaces:**
```python
# Usage in stages
from shared.cost_tracker import CostTracker

tracker = CostTracker()
cost = tracker.log_usage(
    model="gpt-4o",
    tokens_input=1500,
    tokens_output=300,
    job_id="job-123"
)
print(f"Cost: ${cost:.4f}")
```

**Data Model:**
```json
{
  "timestamp": "2025-12-10T10:30:00Z",
  "model_id": "gpt-4o",
  "tokens_input": 1500,
  "tokens_output": 300,
  "cost": 0.063,
  "job_id": "job-123",
  "stage": "13_ai_summarization"
}
```

### FR-2: Budget Management (MUST HAVE)

**Description:** Set and enforce budget limits with automatic alerts

**Components:**
1. **Budget Configuration:**
   - User-level: config/user.profile [budget] section
   - Job-level: Optional per-job limit
   - Organization: config/.env.pipeline MONTHLY_BUDGET

2. **Budget Monitor:**
   - Check budget after every cost update
   - Compare current spend vs. limit
   - Trigger alerts at thresholds

3. **Alert System:**
   - 80% threshold: Warning (log + console)
   - 100% threshold: Critical (log + console + email)
   - Optional blocking: Reject job if at limit

**Configuration:**
```ini
# config/user.profile
[budget]
monthly_limit = 50.00          # USD
alert_threshold = 0.80         # 80%
block_at_limit = false         # Allow overage
notification_email = user@example.com
```

**Alert Format:**
```
⚠️  BUDGET ALERT: 80% Threshold Reached
Current: $40.25 / $50.00 (80.5%)
Remaining: $9.75
Projected month-end: $52.30 (OVER BUDGET)
Recommendation: Reduce usage or increase budget
```

### FR-3: Optimization Engine (SHOULD HAVE)

**Description:** Analyze usage and provide cost reduction recommendations

**Recommendation Types:**

**1. Model Selection:**
```
💡 Optimization Opportunity: Model Downgrade
Current: Using GPT-4 for all summarizations
Recommendation: Use GPT-3.5 for transcripts <5K tokens
Savings: $2.50/month (15% reduction)
Impact: Minimal quality difference for short content
```

**2. Caching:**
```
💡 Optimization Opportunity: Enable Caching
Current: Re-processing similar content
Recommendation: Enable audio fingerprint cache
Savings: $5.00/month (30% reduction)
Impact: 40-95% faster on similar content
```

**3. Batch Processing:**
```
💡 Optimization Opportunity: Batch Jobs
Current: Processing jobs one at a time
Recommendation: Batch 5+ jobs together
Savings: $1.50/month (10% reduction via batch API)
Impact: No quality impact, 20% faster
```

**Recommendation Criteria:**
- Savings ≥5% or $1
- Confidence ≥80%
- Actionable (user can implement)
- No significant quality loss

### FR-4: Historical Analytics (SHOULD HAVE)

**Description:** Analyze cost trends and patterns over time

**Views:**

**1. Cost Trends:**
```
Daily Cost (Last 30 Days)
┌─────────────────────────────────┐
│ $3 │                          ▄▄ │
│ $2 │         ▄▄    ▄▄    ▄▄  █░█ │
│ $1 │   ▄▄   █░█  █░█  █░█ █░█ │
│ $0 │──█░█───█░█──█░█──█░█─█░█─│
│    │ Dec 1    Dec 8   Dec 15  │
└─────────────────────────────────┘
Avg: $2.10/day | Trend: ↑ 15%
```

**2. Cost by Model:**
```
Model Cost Breakdown (December 2025)
─────────────────────────────────────
GPT-4          ████████████  $12.50 (40%)
Whisper API    ████████      $10.00 (32%)
Gemini         ███           $5.00  (16%)
MLX (local)    ██            $3.75  (12%)
─────────────────────────────────────
Total:                       $31.25
```

**3. Cost Forecast:**
```
Month-End Projection
────────────────────
Current (Dec 10): $31.25
Daily avg:        $3.13
Days remaining:   20
Projected total:  $93.85
Budget:           $50.00
Overage:          $43.85 ⚠️

Recommendation: Reduce usage by 50% to stay in budget
```

### FR-5: Cost Reporting (SHOULD HAVE)

**Description:** Generate cost reports for various audiences

**Report Types:**

**1. Monthly Summary:**
```json
{
  "month": "2025-12",
  "total_cost": 93.85,
  "total_tokens": 1250000,
  "jobs_processed": 45,
  "avg_cost_per_job": 2.09,
  "models": {
    "gpt-4o": {"cost": 12.50, "tokens": 50000, "calls": 10},
    "whisper-large-v3": {"cost": 10.00, "tokens": 500000, "calls": 15}
  },
  "workflows": {
    "transcribe": {"cost": 40.00, "jobs": 20},
    "translate": {"cost": 30.00, "jobs": 15},
    "subtitle": {"cost": 23.85, "jobs": 10}
  },
  "optimizations": {
    "recommendations": 5,
    "potential_savings": 28.15,
    "adopted": 2
  }
}
```

**2. Job Cost Receipt:**
```
Job Cost Receipt
────────────────────────────────────
Job ID: job-20251210-rpatel-0001
Workflow: subtitle
Media: movie.mp4
Duration: 2h 15m
────────────────────────────────────
Stage Costs:
  01 Demux              $0.00 (local)
  02 TMDB               $0.00 (cached)
  06 ASR                $2.50 (WhisperX)
  10 Translation        $1.25 (IndicTrans2)
  13 Summarization      $0.75 (GPT-4o)
────────────────────────────────────
Total:                  $4.50
Budget remaining:       $45.50
────────────────────────────────────
```

---

## IV. Non-Functional Requirements

### Performance

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Tracking overhead | <10ms | Time added per API call |
| Report generation | <2s | Monthly report with 1000 jobs |
| Alert latency | <1min | Time from threshold to alert |
| Memory overhead | <50MB | RAM used by cost tracker |

### Scalability

| Requirement | Target | Notes |
|-------------|--------|-------|
| Concurrent users | 1,000 | Cost tracking per user |
| Jobs per month | 10,000 | Per user |
| Data retention | 365 days | 1 year history |
| Storage per user | 10MB/year | Log files |

### Reliability

| Requirement | Target | Strategy |
|-------------|--------|----------|
| Cost tracking accuracy | 100% | Validate against API responses |
| Data integrity | Zero loss | Atomic writes, backups |
| Fault tolerance | Degrade gracefully | Continue if tracking fails |

### Usability

| Requirement | Description |
|-------------|-------------|
| Cost visibility | Costs shown in all relevant UIs |
| Clear alerts | Non-technical language, actionable |
| Easy configuration | Single config file, sensible defaults |
| Export flexibility | JSON, CSV, human-readable formats |

---

## V. Integration Points

### Stage Integration

**Stages That Track Costs:**
- **Stage 06 (ASR):** WhisperX API usage
- **Stage 10 (Translation):** IndicTrans2 (if cloud)
- **Stage 13 (Summarization):** OpenAI/Gemini API

**Integration Pattern:**
```python
# At start of stage
from shared.cost_tracker import CostTracker
tracker = CostTracker(job_id=job_id)

# Before API call
estimate = tracker.estimate_cost(model="gpt-4o", tokens=5000)
logger.info(f"Estimated cost: ${estimate:.4f}")

# After API call
actual_cost = tracker.log_usage(
    model="gpt-4o",
    tokens_input=4800,
    tokens_output=1200,
    job_id=job_id,
    stage="13_ai_summarization"
)
logger.info(f"Actual cost: ${actual_cost:.4f}")

# Check budget
if tracker.is_over_budget():
    logger.warning("Budget threshold reached!")
```

### User Profile Integration (AD-015)

**Budget Configuration:**
```ini
# config/user.profile
[budget]
monthly_limit = 50.00
alert_threshold = 0.80
block_at_limit = false
notification_email = user@example.com

[cost_preferences]
default_model_preference = cheapest  # cheapest | balanced | best
enable_optimization_tips = true
show_cost_estimates = true
```

### Reporting Integration

**Output Locations:**
- **Real-time logs:** `logs/cost-tracking.log`
- **Monthly data:** `logs/cost/{YYYY-MM}.json`
- **Job receipts:** `{job_dir}/cost_receipt.txt`
- **Reports:** `out/reports/cost_report_{YYYY-MM}.html`

---

## VI. User Interface Specs

### CLI Output Examples

**Job Cost Estimate:**
```bash
$ ./prepare-job.sh --media movie.mp4 --workflow subtitle

✅ Job prepared: job-20251210-rpatel-0001

📊 Estimated Costs:
   ASR (WhisperX):       $2.50
   Translation:          $1.25
   Summarization:        $0.75
   ──────────────────────────
   Total:                $4.50

💰 Budget Status:
   Monthly budget:       $50.00
   Current spend:        $31.25
   After this job:       $35.75 (71.5%)
   Remaining:            $14.25

✅ Proceed with job? [Y/n]:
```

**Real-Time Cost Display:**
```bash
$ ./run-pipeline.sh --job-dir out/latest

[10:30:15] Stage 06: ASR
[10:32:40] ✅ ASR complete | Cost: $2.48 | Total job cost: $2.48

[10:32:41] Stage 10: Translation
[10:34:10] ✅ Translation complete | Cost: $1.22 | Total job cost: $3.70

[10:34:11] Stage 13: Summarization
[10:35:05] ✅ Summarization complete | Cost: $0.78 | Total job cost: $4.48

════════════════════════════════════════════════════════════
✅ PIPELINE COMPLETE
   Total cost: $4.48 (within estimate $4.50)
   Budget remaining: $14.27
════════════════════════════════════════════════════════════
```

**Monthly Report:**
```bash
$ ./tools/cost-report.sh --month 2025-12

AI Cost Report - December 2025
════════════════════════════════════════════════════════════

📊 Summary:
   Total cost:           $93.85
   Jobs processed:       45 jobs
   Avg cost per job:     $2.09

💰 Budget Status:
   Monthly limit:        $50.00
   Current spend:        $93.85 (187.7%)
   Overage:              $43.85 ⚠️

📈 Trends:
   Daily average:        $3.13
   vs. last month:       ↑ 25%
   Projected next month: $96.00

💡 Optimization Opportunities:
   1. Switch to Gemini (save $5.20/month)
   2. Enable caching (save $15.00/month)
   3. Use medium model for short content (save $8.00/month)
   Total potential savings: $28.20 (30%)

════════════════════════════════════════════════════════════
💾 Full report: out/reports/cost_report_2025-12.json
```

---

## VII. Testing Requirements

### Unit Tests

- ✅ Cost calculation accuracy
- ✅ Token counting logic
- ✅ Budget threshold detection
- ✅ Recommendation generation
- ✅ Data serialization/deserialization

### Integration Tests

- ✅ Stage integration (cost tracking in pipeline)
- ✅ Alert system (email/log notifications)
- ✅ Report generation (JSON/CSV/HTML)
- ✅ Budget enforcement (blocking behavior)

### End-to-End Tests

- ✅ Full job with cost tracking
- ✅ Budget alert workflow
- ✅ Monthly report generation
- ✅ Optimization recommendation workflow

### Performance Tests

- ✅ Tracking overhead <10ms
- ✅ 1000 concurrent cost updates
- ✅ Report generation <2s
- ✅ Memory usage <50MB

---

## VIII. Acceptance Criteria

### Phase 1: Foundation (MUST HAVE)

- ✅ Track 100% of AI API calls
- ✅ Calculate costs within 1 second
- ✅ Store monthly cost data
- ✅ Configure budgets in user profile
- ✅ Alert at 80% and 100% thresholds
- ✅ Display costs in pipeline logs
- ✅ Generate monthly cost report

### Phase 2: Optimization (SHOULD HAVE)

- ✅ Generate ≥3 recommendations per report
- ✅ Quantify potential savings (%)
- ✅ Track recommendation adoption
- ✅ Compare model costs

### Phase 3: Analytics (NICE TO HAVE)

- ✅ Display cost trends (30 days)
- ✅ Forecast month-end costs
- ✅ Calculate ROI metrics
- ✅ Export reports (JSON/CSV)

---

## IX. Release Plan

### Phase 1: MVP (Week 1 - 4 hours)

**Deliverables:**
- Enhanced cost tracking module
- Budget management
- Alert system
- CLI integration

### Phase 2: Optimization (Week 2 - 2 hours)

**Deliverables:**
- Recommendation engine
- Model comparison
- Optimization reports

### Phase 3: Analytics (Week 3 - 2 hours - OPTIONAL)

**Deliverables:**
- Historical trends
- Cost forecasting
- ROI dashboard

---

**Status:** Draft → Pending Approval

**Related Documents:**
- [BRD-2025-12-10-04-cost-tracking](../brd/BRD-2025-12-10-04-cost-tracking.md)
- TRD-2025-12-10-04-cost-tracking.md (to be created)

**Next Steps:**
1. Review and approve PRD
2. Create TRD with technical design
3. Implement Phase 1 foundation
4. Test and validate
5. Deploy to production
