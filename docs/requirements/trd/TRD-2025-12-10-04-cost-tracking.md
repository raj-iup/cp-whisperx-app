# Technical Requirements Document: Cost Tracking & Optimization

**TRD ID:** TRD-2025-12-10-04-cost-tracking  
**Created:** 2025-12-10  
**Status:** Draft  
**Related BRD:** [BRD-2025-12-10-04-cost-tracking](../brd/BRD-2025-12-10-04-cost-tracking.md)  
**Related PRD:** [PRD-2025-12-10-04-cost-tracking](../prd/PRD-2025-12-10-04-cost-tracking.md)

---

## I. Technical Overview

### Summary

Implement comprehensive cost tracking and optimization system for all AI services (OpenAI, Gemini, WhisperX, IndicTrans2) with real-time monitoring, budget management, and optimization recommendations.

**Key Capabilities:**
- Real-time cost tracking (<1 min latency)
- Budget alerts at 80%/100% thresholds
- Optimization recommendations (15-30% savings)
- Historical analytics and forecasting
- ROI reporting

### Approach

**3-Tier Architecture:**
```
┌─────────────────────────────────────────────┐
│ Layer 1: Data Collection (Stages)          │
│  - Track API calls and token usage         │
│  - Log costs in real-time                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Layer 2: Cost Tracking Core (shared/)      │
│  - CostTracker class (API)                 │
│  - Cost computation logic                  │
│  - Budget monitoring                       │
│  - Data persistence (JSON/SQLite)          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Layer 3: Reporting & Optimization (tools/) │
│  - Cost dashboard                          │
│  - Optimization engine                     │
│  - Historical analytics                    │
│  - Budget alerts                           │
└─────────────────────────────────────────────┘
```

### Key Technologies

- **Python 3.11+:** Core implementation language
- **JSON:** Configuration and data storage (Phase 1)
- **SQLite:** Cost history database (Phase 2 - optional)
- **tabulate:** Console table formatting
- **matplotlib:** Cost trend visualization (Phase 2)

---

## II. Architecture Changes

### Affected Components

```
┌─────────────────────────────────────────────────────────────┐
│ Existing Stages (Modified)                                 │
│  - scripts/06_whisperx_asr.py (add cost tracking)          │
│  - scripts/10_translation.py (add cost tracking)           │
│  - scripts/13_ai_summarization.py (add cost tracking)      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ NEW: Cost Tracking Core (shared/cost_tracker.py)           │
│  - CostTracker class                                        │
│  - log_usage(), get_job_cost(), check_budget_alerts()      │
│  - Cost computation + persistence                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ NEW: Cost Dashboard (tools/cost-dashboard.py)              │
│  - show_job_costs(), show_monthly_summary()                │
│  - show_optimization_recommendations()                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Configuration (Modified)                                    │
│  - config/.env.pipeline (add cost parameters)              │
│  - users/<userId>/profile.json (add budget field)          │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

**1. Stage Integration:**
```python
# In scripts/06_whisperx_asr.py, 10_translation.py, 13_ai_summarization.py
from shared.cost_tracker import CostTracker

def run_stage(job_dir: Path, stage_name: str) -> int:
    tracker = CostTracker(job_dir)
    
    # Track API call
    cost = tracker.log_usage(
        service="openai",
        model="gpt-4o",
        tokens_input=1500,
        tokens_output=300,
        stage=stage_name
    )
    
    logger.info(f"💰 Stage cost: ${cost:.4f}")
```

**2. Configuration Integration:**
```bash
# config/.env.pipeline
COST_TRACKING_ENABLED=true
MONTHLY_BUDGET_USD=50.00
COST_ALERT_THRESHOLD=80
COST_STORAGE_PATH=~/.cp-whisperx/costs
```

**3. User Profile Integration:**
```json
{
  "user_id": 1,
  "budget": {
    "monthly_limit_usd": 50.00,
    "alert_threshold_percent": 80,
    "block_at_limit": false
  }
}
```

### Data Flow

```
API Call → Token Count → Cost Calculation → Log Entry → Budget Check
   ↓            ↓              ↓               ↓           ↓
Stage     CostTracker    Pricing DB      JSON File   Alert System
```

**Detailed Flow:**
1. **Stage calls AI API** (OpenAI, Gemini, WhisperX)
2. **Track tokens:** Input tokens, output tokens, model name
3. **Compute cost:** Look up pricing, calculate cost
4. **Log usage:** Append to cost history JSON
5. **Check budget:** Compare current spend vs. limit
6. **Alert if needed:** Warning at 80%, critical at 100%

---

## III. Design Decisions

### Decision 1: Storage Format (JSON vs. SQLite)

**Problem:** Need to store cost history efficiently

**Options:**
1. **JSON files** - ✅ Selected
   - Simple, no dependencies
   - Human-readable for debugging
   - Fast for typical usage (<10K entries)
   - Easy migration to SQLite later

2. **SQLite** - ❌ Deferred to Phase 2
   - Better for large datasets (>10K entries)
   - Complex queries (trends, aggregations)
   - Adds dependency

**Rationale:** Start with JSON for simplicity. Most users will have <1000 cost entries/month. Can migrate to SQLite in Phase 2 if needed.

**Implementation:**
```python
# File structure
~/.cp-whisperx/costs/
  ├── 2025-12.json          # Monthly cost log
  ├── current.json          # Current month (symlink)
  └── summary.json          # Aggregated totals
```

### Decision 2: Real-Time vs. Batch Tracking

**Problem:** When to update cost records

**Options:**
1. **Real-time (per API call)** - ✅ Selected
   - Immediate cost visibility
   - Accurate budget monitoring
   - Simple implementation

2. **Batch (end of job)** - ❌ Rejected
   - Delayed visibility
   - Cannot prevent budget overruns
   - More complex state management

**Rationale:** Real-time tracking enables immediate budget alerts and prevents cost overruns. Performance impact is negligible (1-2ms per API call).

### Decision 3: Budget Enforcement (Soft vs. Hard Limits)

**Problem:** Should system block jobs at budget limit?

**Options:**
1. **Soft limits (alert only)** - ✅ Selected (default)
   - User control, no surprise failures
   - Flexible for important jobs
   - Configurable per user

2. **Hard limits (block jobs)** - ✅ Optional (user choice)
   - Strict budget compliance
   - Risk of blocking critical work
   - Can be enabled via config

**Rationale:** Default to soft limits (alerts only) for flexibility. Allow users to opt-in to hard limits via `block_at_limit=true` in profile.

**Implementation:**
```python
def check_budget(user_id: int, job_cost: float) -> tuple[bool, str]:
    """Check if job is within budget. Returns (allowed, message)."""
    profile = load_user_profile(user_id)
    budget = profile["budget"]
    current_spend = get_monthly_spend(user_id)
    
    if current_spend + job_cost > budget["monthly_limit_usd"]:
        if budget.get("block_at_limit", False):
            return False, "❌ Budget limit reached. Job blocked."
        else:
            return True, "⚠️ Budget limit exceeded. Job allowed (soft limit)."
    
    return True, "✅ Within budget"
```

---

## IV. Implementation Requirements

### Code Changes

#### New Files

**1. Core Cost Tracker (300-400 lines)**
```python
# shared/cost_tracker.py
class CostTracker:
    """Track AI service costs across jobs and stages."""
    
    def __init__(self, job_dir: Path = None, user_id: int = 1):
        """Initialize cost tracker for job or user."""
        self.job_dir = job_dir
        self.user_id = user_id
        self.cost_db = self._load_cost_database()
    
    def log_usage(
        self,
        service: str,
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        stage: str = None
    ) -> float:
        """Log API usage and return cost."""
        cost = self._compute_cost(service, model, tokens_input, tokens_output)
        self._append_log_entry(...)
        self._check_budget_alerts()
        return cost
    
    def get_job_cost(self, job_id: str) -> float:
        """Get total cost for job."""
        
    def get_monthly_cost(self, user_id: int = None) -> float:
        """Get total cost for current month."""
    
    def check_budget_alerts(self, user_id: int = None) -> list[str]:
        """Check budget thresholds and return alerts."""
    
    def _compute_cost(self, service: str, model: str, tokens_in: int, tokens_out: int) -> float:
        """Compute cost based on pricing database."""
        pricing = self.cost_db["pricing"][service][model]
        cost_input = tokens_in / 1000 * pricing["input_per_1k"]
        cost_output = tokens_out / 1000 * pricing["output_per_1k"]
        return cost_input + cost_output
```

**2. Cost Dashboard Tool (200-300 lines)**
```python
# tools/cost-dashboard.py
def show_job_costs(job_id: str = None):
    """Show cost breakdown for job(s)."""
    
def show_monthly_summary(month: str = None):
    """Show monthly cost summary."""
    
def show_optimization_recommendations():
    """Show cost optimization suggestions."""
    
def export_cost_report(format: str = "json"):
    """Export cost report (json, csv, pdf)."""
```

**3. Optimization Engine (Phase 2 - 200-300 lines)**
```python
# shared/cost_optimizer.py
class CostOptimizer:
    """Analyze usage and provide cost reduction recommendations."""
    
    def analyze_usage(self, user_id: int) -> dict:
        """Analyze user's cost patterns."""
        
    def recommend_model_changes(self) -> list[dict]:
        """Recommend cheaper model alternatives."""
        
    def recommend_caching(self) -> list[dict]:
        """Recommend caching opportunities."""
```

**4. Unit Tests (150-200 lines)**
```python
# tests/unit/test_cost_tracker.py
class TestCostTracker:
    def test_log_usage_openai(self):
        """Test OpenAI cost tracking."""
        
    def test_log_usage_gemini(self):
        """Test Gemini cost tracking."""
        
    def test_budget_alert_80_percent(self):
        """Test budget alert at 80% threshold."""
        
    def test_budget_alert_100_percent(self):
        """Test budget alert at 100% threshold."""
        
    def test_get_monthly_cost(self):
        """Test monthly cost aggregation."""
```

#### Modified Files

**1. Stage 06 (WhisperX ASR):**
```python
# scripts/06_whisperx_asr.py
from shared.cost_tracker import CostTracker

def run_stage(job_dir: Path, stage_name: str = "06_whisperx_asr") -> int:
    # ... existing code ...
    tracker = CostTracker(job_dir)
    
    # Track WhisperX API cost (if using API)
    if use_whisperx_api:
        cost = tracker.log_usage(
            service="whisperx",
            model="large-v3",
            tokens_input=audio_duration_seconds * 50,  # Approximate
            stage=stage_name
        )
        logger.info(f"💰 ASR cost: ${cost:.4f}")
```

**2. Stage 10 (Translation):**
```python
# scripts/10_translation.py
from shared.cost_tracker import CostTracker

def run_stage(job_dir: Path, stage_name: str = "10_translation") -> int:
    # ... existing code ...
    tracker = CostTracker(job_dir)
    
    # Track IndicTrans2 cost (local = $0, API = cost)
    if use_indictrans2_api:
        cost = tracker.log_usage(
            service="indictrans2",
            model="en-indic",
            tokens_input=total_tokens,
            stage=stage_name
        )
        logger.info(f"💰 Translation cost: ${cost:.4f}")
    else:
        # Local processing - track as $0
        tracker.log_usage(
            service="local",
            model="indictrans2-local",
            tokens_input=0,
            tokens_output=0,
            stage=stage_name
        )
```

**3. Stage 13 (AI Summarization):**
```python
# scripts/13_ai_summarization.py
from shared.cost_tracker import CostTracker

def run_stage(job_dir: Path, stage_name: str = "13_ai_summarization") -> int:
    # ... existing code ...
    tracker = CostTracker(job_dir)
    
    # Track OpenAI/Gemini cost
    response = openai.ChatCompletion.create(...)
    cost = tracker.log_usage(
        service="openai",
        model="gpt-4o",
        tokens_input=response.usage.prompt_tokens,
        tokens_output=response.usage.completion_tokens,
        stage=stage_name
    )
    logger.info(f"💰 Summarization cost: ${cost:.4f}")
```

### Configuration Changes

**1. System Configuration:**
```bash
# config/.env.pipeline (add to end of AI Services section)

# ════════════════════════════════════════════════════════════════
# COST TRACKING & OPTIMIZATION
# ════════════════════════════════════════════════════════════════
# Status: ✅ Implemented (Phase 5 - Task #21)
# Related: shared/cost_tracker.py, tools/cost-dashboard.py

# Enable/disable cost tracking
COST_TRACKING_ENABLED=true
# Type: boolean | Default: true | Impact: Disables all cost tracking

# Default monthly budget (USD)
MONTHLY_BUDGET_USD=50.00
# Type: float | Default: 50.00 | Impact: Default budget for new users

# Budget alert threshold (percent)
COST_ALERT_THRESHOLD=80
# Type: int (0-100) | Default: 80 | Impact: Alert at 80% of budget

# Cost storage directory
COST_STORAGE_PATH=~/.cp-whisperx/costs
# Type: path | Default: ~/.cp-whisperx/costs | Impact: Where cost logs are stored

# Block jobs at budget limit
BLOCK_AT_BUDGET_LIMIT=false
# Type: boolean | Default: false | Impact: Hard vs soft budget limits

# Cost optimization recommendations
ENABLE_COST_OPTIMIZATION=true
# Type: boolean | Default: true | Impact: Show cost-saving recommendations
```

**2. User Profile:**
```json
// users/<userId>/profile.json
{
  "user_id": 1,
  "name": "Default User",
  "email": "user@example.com",
  "credentials": {
    // ... existing credentials ...
  },
  "budget": {
    "monthly_limit_usd": 50.00,
    "alert_threshold_percent": 80,
    "block_at_limit": false,
    "notification_email": "user@example.com"
  },
  "cost_preferences": {
    "show_estimates": true,
    "show_realtime_costs": true,
    "optimization_recommendations": true
  }
}
```

### Dependencies

**No new dependencies required!** Using Python standard library only.

**Optional (Phase 2):**
```txt
# requirements/cost-tracking.txt (Phase 2 - optional)
matplotlib>=3.8.0       # Cost trend visualization
tabulate>=0.9.0         # Pretty table formatting (already installed)
```

---

## V. Testing Requirements

### Unit Tests (≥80% coverage)

**Test File:** `tests/unit/test_cost_tracker.py`

```python
#!/usr/bin/env python3
"""Unit tests for cost tracking module."""

import pytest
from pathlib import Path
from shared.cost_tracker import CostTracker

class TestCostTracker:
    """Test CostTracker class."""
    
    def test_init_with_job_dir(self, tmp_path):
        """Test initialization with job directory."""
        tracker = CostTracker(job_dir=tmp_path)
        assert tracker.job_dir == tmp_path
        assert tracker.user_id == 1  # Default
    
    def test_log_usage_openai_gpt4(self):
        """Test OpenAI GPT-4 cost computation."""
        tracker = CostTracker()
        cost = tracker.log_usage(
            service="openai",
            model="gpt-4o",
            tokens_input=1000,
            tokens_output=200
        )
        # GPT-4o: $0.03/1K input, $0.06/1K output
        expected = (1000/1000 * 0.03) + (200/1000 * 0.06)
        assert abs(cost - expected) < 0.001
    
    def test_log_usage_gemini(self):
        """Test Gemini cost computation."""
        tracker = CostTracker()
        cost = tracker.log_usage(
            service="gemini",
            model="gemini-1.5-pro",
            tokens_input=1000,
            tokens_output=200
        )
        # Gemini: $0.00025/1K tokens (combined)
        expected = (1000 + 200) / 1000 * 0.00025
        assert abs(cost - expected) < 0.001
    
    def test_budget_alert_80_percent(self):
        """Test budget alert at 80% threshold."""
        tracker = CostTracker(user_id=1)
        # Simulate usage up to 80%
        for i in range(40):  # $40 of $50 budget
            tracker.log_usage("openai", "gpt-4o", 1000, 0)
        
        alerts = tracker.check_budget_alerts()
        assert len(alerts) == 1
        assert "80%" in alerts[0]
    
    def test_budget_alert_100_percent(self):
        """Test budget alert at 100% threshold."""
        tracker = CostTracker(user_id=1)
        # Simulate usage up to 100%
        for i in range(50):  # $50 of $50 budget
            tracker.log_usage("openai", "gpt-4o", 1000, 0)
        
        alerts = tracker.check_budget_alerts()
        assert len(alerts) >= 2  # Both 80% and 100%
        assert any("100%" in alert for alert in alerts)
    
    def test_get_job_cost(self, tmp_path):
        """Test job cost aggregation."""
        job_dir = tmp_path / "job-123"
        job_dir.mkdir()
        
        tracker = CostTracker(job_dir=job_dir)
        tracker.log_usage("openai", "gpt-4o", 1000, 200)
        tracker.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        
        total = tracker.get_job_cost("job-123")
        assert total > 0
    
    def test_get_monthly_cost(self):
        """Test monthly cost aggregation."""
        tracker = CostTracker(user_id=1)
        
        # Log some usage
        tracker.log_usage("openai", "gpt-4o", 1000, 200)
        tracker.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        
        monthly = tracker.get_monthly_cost()
        assert monthly > 0
    
    def test_local_processing_zero_cost(self):
        """Test local processing (MLX, IndicTrans2) has zero cost."""
        tracker = CostTracker()
        cost = tracker.log_usage(
            service="local",
            model="mlx-whisper",
            tokens_input=0,
            tokens_output=0
        )
        assert cost == 0.0
```

### Integration Tests

**Test File:** `tests/integration/test_cost_tracking_e2e.py`

**Scenario 1: Full job with cost tracking**
```python
def test_cost_tracking_full_job(test_media_sample):
    """Test cost tracking through full job execution."""
    # Run prepare-job with cost tracking enabled
    job_id = prepare_job(
        media=test_media_sample,
        workflow="transcribe",
        user_id=1
    )
    
    # Run pipeline
    result = run_pipeline(job_id)
    assert result == 0
    
    # Check costs were tracked
    tracker = CostTracker()
    job_cost = tracker.get_job_cost(job_id)
    assert job_cost > 0
    
    # Verify cost breakdown
    costs = tracker.get_stage_costs(job_id)
    assert "06_whisperx_asr" in costs
```

**Scenario 2: Budget alert during job**
```python
def test_budget_alert_during_job(test_media_sample):
    """Test budget alert is triggered during expensive job."""
    # Set low budget
    profile = load_user_profile(1)
    profile["budget"]["monthly_limit_usd"] = 5.00
    save_user_profile(profile)
    
    # Run expensive job
    job_id = prepare_job(
        media=test_media_sample,
        workflow="subtitle",
        user_id=1
    )
    
    # Check for budget alert in logs
    logs = get_job_logs(job_id)
    assert "⚠️ BUDGET ALERT" in logs
```

### Manual Testing

**Script:** `tests/manual/cost-tracking/test-cost-tracking.sh`

```bash
#!/bin/bash
# Manual test for cost tracking feature

echo "🧪 Testing Cost Tracking"

# Test 1: Run job with cost tracking
echo "Test 1: Run transcribe job with cost tracking"
./prepare-job.sh \
  --media in/test_clips/sample.mp4 \
  --workflow transcribe \
  --user-id 1

# Test 2: Check job cost
echo "Test 2: Check job cost"
python3 tools/cost-dashboard.py show-job-costs

# Test 3: Check monthly summary
echo "Test 3: Check monthly summary"
python3 tools/cost-dashboard.py show-monthly-summary

# Test 4: Budget alert
echo "Test 4: Trigger budget alert"
python3 tools/cost-dashboard.py set-budget 1.00
./run-pipeline.sh job-*/  # Should trigger alert

echo "✅ Cost tracking tests complete"
```

---

## VI. Documentation Updates

### Required Updates

- [x] **ARCHITECTURE.md** - Add Cost Tracking section
  - Cost tracking architecture
  - Data flow diagrams
  - Storage format

- [x] **DEVELOPER_STANDARDS.md** - Add cost tracking patterns
  - How to add cost tracking to stages
  - CostTracker API usage
  - Testing requirements

- [x] **User Guide** - Add cost management section
  - Setting budgets
  - Viewing cost reports
  - Understanding cost optimization

- [x] **Configuration Guide** - Document new parameters
  - COST_TRACKING_ENABLED
  - MONTHLY_BUDGET_USD
  - COST_ALERT_THRESHOLD

- [x] **IMPLEMENTATION_TRACKER.md** - Add Task #21
  - Cost Tracking Module (6-8 hours)
  - Status, progress, completion criteria

- [x] **Copilot Instructions** - Add cost tracking rules
  - Always add cost tracking to AI-using stages
  - Use CostTracker.log_usage() pattern

---

## VII. Performance Considerations

### Processing Time Impact

**Cost Tracking Overhead:**
- **Per API call:** +1-2ms (JSON append + computation)
- **Per job:** +10-20ms total (multiple API calls)
- **Impact:** Negligible (<0.1% of total job time)

**Optimization:**
- Batch writes (append every 10 calls)
- In-memory aggregation
- Async JSON writes (Phase 2)

### Memory Usage Impact

**Memory Overhead:**
- **CostTracker instance:** ~1-2 KB
- **Cost history (in-memory):** ~100 KB per 1000 entries
- **Impact:** Minimal (<5 MB for typical jobs)

**Optimization:**
- Stream large cost logs (don't load all into memory)
- Periodic cleanup of old entries (>90 days)

---

## VIII. Security Considerations

### Sensitive Data

**Cost data is NOT sensitive but budget limits may be:**
- ✅ Cost logs stored in user directory (`users/<userId>/costs/`)
- ✅ Budget limits in user profile (already secured)
- ❌ No API keys or credentials in cost logs

### Access Control

**Cost data access:**
- Each user can only see their own costs
- Admin user (userId=0) can see all costs
- Cost logs stored per-user, not globally

### Data Privacy

**No external sharing:**
- ✅ Cost data stays local (never sent to cloud)
- ✅ No analytics or telemetry
- ✅ User controls all cost data

---

## IX. Rollback Plan

### If cost tracking fails:

**Step 1: Disable cost tracking**
```bash
# config/.env.pipeline
COST_TRACKING_ENABLED=false
```

**Step 2: Remove from stages**
```bash
git revert <commit-hash>  # Revert stage integration commits
```

**Step 3: Clean up cost logs (optional)**
```bash
rm -rf ~/.cp-whisperx/costs/
```

**Step 4: Restore configuration**
```bash
git checkout config/.env.pipeline
```

**Recovery time:** <5 minutes  
**Data loss:** Cost history only (no pipeline data affected)

---

## X. Implementation Phases

### Phase 1: Core Implementation (6-8 hours) ← **START HERE**

**Week 3 (2025-12-10 to 2025-12-16):**

**Day 1-2: Core Module (3-4 hours)**
- ✅ Create `shared/cost_tracker.py`
- ✅ Implement CostTracker class
- ✅ Add pricing database (JSON)
- ✅ Implement log_usage(), get_job_cost(), check_budget_alerts()

**Day 3: Stage Integration (2 hours)**
- ✅ Update Stage 06 (WhisperX ASR)
- ✅ Update Stage 10 (Translation)
- ✅ Update Stage 13 (AI Summarization)

**Day 4: Dashboard (1-2 hours)**
- ✅ Create `tools/cost-dashboard.py`
- ✅ Implement show_job_costs()
- ✅ Implement show_monthly_summary()

**Day 5: Testing (1 hour)**
- ✅ Write unit tests (≥80% coverage)
- ✅ Run integration tests
- ✅ Manual testing with real jobs

**Deliverables:**
- ✅ shared/cost_tracker.py (300-400 lines)
- ✅ tools/cost-dashboard.py (200-300 lines)
- ✅ tests/unit/test_cost_tracker.py (150-200 lines)
- ✅ Stage integration (3 files modified)
- ✅ Configuration updates (2 files modified)

### Phase 2: Advanced Features (4-6 hours) ← **OPTIONAL**

**Week 4 (2025-12-17 to 2025-12-23):**

**Optimization Engine (2-3 hours)**
- ✅ Create `shared/cost_optimizer.py`
- ✅ Implement recommendation engine
- ✅ Add optimization dashboard

**Historical Analytics (2-3 hours)**
- ✅ Add trend analysis
- ✅ Cost forecasting
- ✅ Visualization (matplotlib)

---

## XI. Related Documents

- **BRD:** [BRD-2025-12-10-04-cost-tracking.md](../brd/BRD-2025-12-10-04-cost-tracking.md)
- **PRD:** [PRD-2025-12-10-04-cost-tracking.md](../prd/PRD-2025-12-10-04-cost-tracking.md)
- **Implementation Tracker:** [IMPLEMENTATION_TRACKER.md](../../../IMPLEMENTATION_TRACKER.md)
- **Architecture:** [ARCHITECTURE.md](../../../ARCHITECTURE.md)

---

## XII. Implementation Checklist

### Pre-Implementation
- [x] BRD approved (BRD-2025-12-10-04-cost-tracking.md)
- [x] PRD complete (PRD-2025-12-10-04-cost-tracking.md)
- [x] TRD reviewed (this document)
- [x] Dependencies identified (none required)

### During Implementation (Phase 1)
- [ ] Create shared/cost_tracker.py
- [ ] Create tools/cost-dashboard.py
- [ ] Update Stage 06 (WhisperX ASR)
- [ ] Update Stage 10 (Translation)
- [ ] Update Stage 13 (AI Summarization)
- [ ] Add configuration parameters
- [ ] Write unit tests (≥80% coverage)
- [ ] Write integration tests
- [ ] Update documentation

### Post-Implementation
- [ ] All unit tests passing (≥80% coverage)
- [ ] All integration tests passing
- [ ] Manual testing complete
- [ ] Documentation updated (6 files)
- [ ] IMPLEMENTATION_TRACKER.md updated
- [ ] Code review complete
- [ ] PR approved and merged

### Phase 2 (Optional)
- [ ] Optimization engine implemented
- [ ] Historical analytics implemented
- [ ] Visualization added (matplotlib)
- [ ] Advanced reports created

---

**Version:** 1.0  
**Status:** Draft → Ready for Implementation  
**Estimated Time:** 6-8 hours (Phase 1), 4-6 hours (Phase 2 - optional)  
**Priority:** 🔥 HIGH (Foundation for Phase 6)  
**Next Step:** Begin Phase 1 implementation (create shared/cost_tracker.py)
