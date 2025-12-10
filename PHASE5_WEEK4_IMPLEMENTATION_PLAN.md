# Phase 5 Week 4 - Implementation Plan & Status

**Date:** 2025-12-10  
**Status:** 📋 PLANNED  
**Selected Option:** A (All 3 Features)

---

## 🎯 Week 4 Goals

### **Feature 1: Real-Time Cost Display in Pipeline** 💰
**Time:** 2-3 hours  
**Status:** 📋 Planned  
**Priority:** HIGH

#### **Implementation Tasks:**
1. ✅ Locate pipeline runner (`scripts/run-pipeline.py` - 143KB)
2. ⏳ Add cost tracker import
3. ⏳ Read job costs after each stage completes
4. ⏳ Display cost in pipeline log
5. ⏳ Show running total
6. ⏳ Display budget status

#### **Implementation Details:**

**File to Modify:** `scripts/run-pipeline.py`

**Location:** After each stage completion (search for "Stage.*COMPLETED" or equivalent)

**Code to Add:**
```python
from shared.cost_tracker import CostTracker

# After stage completes
def display_stage_cost(job_dir, stage_name, user_id=1):
    """Display cost for completed stage."""
    try:
        tracker = CostTracker(job_dir=job_dir, user_id=user_id)
        
        # Get latest cost entry for this stage
        month = datetime.now().strftime("%Y-%m")
        cost_file = Path(f"users/{user_id}/costs/{month}.json")
        
        if cost_file.exists():
            with open(cost_file) as f:
                costs = json.load(f)
            
            # Get stage cost
            stage_costs = costs.get("by_stage", {}).get(stage_name, {})
            stage_cost = stage_costs.get("cost", 0.0)
            
            # Get monthly total
            total_cost = costs.get("total_cost", 0.0)
            
            # Get budget info
            summary = tracker.get_monthly_summary(user_id)
            budget = summary.get("budget_limit", 50.0)
            percent_used = (total_cost / budget * 100) if budget > 0 else 0
            
            # Display cost
            logger.info(f"💰 Stage cost: ${stage_cost:.4f}")
            logger.info(f"   Running total: ${total_cost:.2f}")
            logger.info(f"   Budget status: {percent_used:.1f}% of ${budget:.2f} monthly limit")
            
            # Alert if over 80%
            if percent_used >= 80:
                if percent_used >= 100:
                    logger.warning(f"🚨 Budget limit reached! ${total_cost:.2f} / ${budget:.2f}")
                else:
                    logger.warning(f"⚠️  Budget alert: {percent_used:.1f}% used")
    except Exception as e:
        logger.debug(f"Could not display cost: {e}")
```

**Where to Call:**
```python
# In run-pipeline.py, after stage completion
if stage_result == 0:  # Success
    logger.info(f"✅ Stage {stage_name}: COMPLETED ({elapsed:.1f}s)")
    
    # NEW: Display cost
    display_stage_cost(job_dir, stage_name, user_id)
```

---

### **Feature 2: Cost Prediction Before Execution** 📊
**Time:** 3-4 hours  
**Status:** 📋 Planned  
**Priority:** HIGH

#### **Implementation Tasks:**
1. ⏳ Create cost estimator module (`shared/cost_estimator.py`)
2. ⏳ Estimate based on audio duration + workflow
3. ⏳ Add `--estimate-only` flag to `prepare-job.sh`
4. ⏳ Display estimate before job creation
5. ⏳ Interactive confirmation prompt
6. ⏳ Tests

#### **Implementation Details:**

**New File:** `shared/cost_estimator.py`

```python
#!/usr/bin/env python3
"""
Cost Estimator - Predict job costs before execution

Estimates costs based on:
- Audio duration
- Workflow type
- Enabled stages
- Model selection
"""

from pathlib import Path
from typing import Dict, Tuple
import wave

from shared.cost_tracker import PRICING_DATABASE
from shared.logger import get_logger

logger = get_logger(__name__)


class CostEstimator:
    """Estimate job costs before execution."""
    
    def __init__(self):
        self.pricing = PRICING_DATABASE
    
    def estimate_asr_cost(self, duration_sec: float, model: str = "large-v3") -> float:
        """
        Estimate ASR cost (local = $0.00).
        
        Args:
            duration_sec: Audio duration in seconds
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Local ASR (MLX, WhisperX) = $0.00
        return 0.0
    
    def estimate_translation_cost(self, segment_count: int, target_langs: list) -> float:
        """
        Estimate translation cost (local IndicTrans2 = $0.00).
        
        Args:
            segment_count: Number of segments to translate
            target_langs: List of target languages
            
        Returns:
            Estimated cost in USD
        """
        # Local IndicTrans2 = $0.00
        return 0.0
    
    def estimate_summarization_cost(
        self, 
        transcript_length: int, 
        provider: str = "openai",
        model: str = "gpt-4o"
    ) -> float:
        """
        Estimate AI summarization cost.
        
        Args:
            transcript_length: Transcript character count
            provider: AI provider (openai, gemini)
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        estimated_tokens = transcript_length / 4
        
        # Typical split: 80% input, 20% output for summarization
        input_tokens = int(estimated_tokens * 0.8)
        output_tokens = int(estimated_tokens * 0.2)
        
        # Get pricing
        provider_pricing = self.pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, {})
        
        input_cost_per_1k = model_pricing.get("input_per_1k", 0.01)
        output_cost_per_1k = model_pricing.get("output_per_1k", 0.03)
        
        # Calculate cost
        cost = (
            (input_tokens / 1000) * input_cost_per_1k +
            (output_tokens / 1000) * output_cost_per_1k
        )
        
        return cost
    
    def estimate_job_cost(
        self,
        audio_path: Path,
        workflow: str,
        target_langs: list = None,
        enable_summarization: bool = False
    ) -> Tuple[Dict[str, float], float]:
        """
        Estimate total job cost.
        
        Args:
            audio_path: Path to audio file
            workflow: Workflow name (transcribe/translate/subtitle)
            target_langs: List of target languages
            enable_summarization: Whether AI summarization is enabled
            
        Returns:
            Tuple of (breakdown dict, total cost)
        """
        breakdown = {}
        
        # Get audio duration
        try:
            with wave.open(str(audio_path), 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration_sec = frames / float(rate)
        except Exception:
            # Fallback: estimate from file size (rough)
            duration_sec = audio_path.stat().st_size / 176400  # 44.1kHz stereo 16-bit
        
        # Stage costs
        breakdown["demux"] = 0.0  # Local
        breakdown["tmdb"] = 0.0  # API but free tier
        breakdown["glossary_load"] = 0.0  # Local
        breakdown["source_separation"] = 0.0  # Local Demucs
        breakdown["pyannote_vad"] = 0.0  # Local
        breakdown["asr"] = self.estimate_asr_cost(duration_sec)
        breakdown["alignment"] = 0.0  # Local
        
        if workflow in ["translate", "subtitle"]:
            # Estimate segments (rough: 1 segment per 5 seconds of speech)
            segment_count = int(duration_sec / 5)
            breakdown["translation"] = self.estimate_translation_cost(
                segment_count, 
                target_langs or ["en"]
            )
        
        if workflow == "subtitle":
            breakdown["subtitle_generation"] = 0.0  # Local
            breakdown["mux"] = 0.0  # Local
        
        if enable_summarization:
            # Estimate transcript length (rough: 150 words per minute)
            minutes = duration_sec / 60
            word_count = int(minutes * 150)
            char_count = word_count * 6  # Average word length + space
            
            breakdown["ai_summarization"] = self.estimate_summarization_cost(
                char_count,
                provider="openai",
                model="gpt-4o"
            )
        
        total = sum(breakdown.values())
        return breakdown, total


def show_cost_estimate(
    audio_path: Path,
    workflow: str,
    target_langs: list = None,
    enable_summarization: bool = False,
    budget: float = 50.0
):
    """
    Display cost estimate to user.
    
    Args:
        audio_path: Path to audio file
        workflow: Workflow name
        target_langs: Target languages
        enable_summarization: Whether summarization enabled
        budget: Monthly budget limit
    """
    estimator = CostEstimator()
    breakdown, total = estimator.estimate_job_cost(
        audio_path, workflow, target_langs, enable_summarization
    )
    
    print("\n" + "=" * 60)
    print("💰 Estimated Job Cost")
    print("=" * 60)
    
    # Show non-zero costs only
    for stage, cost in breakdown.items():
        if cost > 0:
            print(f"   {stage:25s} ${cost:.4f}")
    
    print("   " + "-" * 58)
    print(f"   {'Total Estimated':25s} ${total:.4f}")
    print()
    
    # Budget info
    percent = (total / budget * 100) if budget > 0 else 0
    remaining = budget - total
    
    print(f"   Current budget:          ${budget:.2f}")
    print(f"   Remaining after job:     ${remaining:.2f} ({100-percent:.1f}%)")
    print("=" * 60)
    print()
    
    return total
```

**Integration in `prepare-job.sh`:**

```bash
# Add flag handling
ESTIMATE_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --estimate-only)
            ESTIMATE_ONLY=true
            shift
            ;;
        # ... other flags
    esac
done

# After media validation, before job creation
if [ "$ESTIMATE_ONLY" = true ]; then
    log_info "Estimating job cost..."
    
    python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')

from shared.cost_estimator import show_cost_estimate

audio_path = Path('$MEDIA_FILE')
workflow = '$WORKFLOW'
target_langs = '${TARGET_LANGS}'.split(',') if '${TARGET_LANGS}' else []
enable_summarization = ${ENABLE_SUMMARIZATION:-False}

total = show_cost_estimate(
    audio_path, workflow, target_langs, enable_summarization
)

# Exit with special code to indicate estimation only
sys.exit(10)
"
    
    exit_code=$?
    if [ $exit_code -eq 10 ]; then
        log_info "Estimation complete (use without --estimate-only to proceed)"
        exit 0
    fi
fi
```

---

### **Feature 3: YouTube Playlist Support** 📺
**Time:** 6-8 hours  
**Status:** 📋 Planned  
**Priority:** MEDIUM

#### **Implementation Tasks:**
1. ⏳ Detect playlist URLs
2. ⏳ Parse playlist with yt-dlp
3. ⏳ Iterate through videos
4. ⏳ Create multiple jobs
5. ⏳ Progress tracking
6. ⏳ Batch execution option
7. ⏳ Tests + Documentation

#### **Implementation Details:**

**Enhance:** `shared/online_downloader.py`

```python
def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist."""
    return 'playlist?list=' in url or '&list=' in url


def get_playlist_videos(playlist_url: str) -> List[Dict[str, str]]:
    """
    Get list of videos in a playlist.
    
    Args:
        playlist_url: YouTube playlist URL
        
    Returns:
        List of dicts with video_id, title, url
    """
    try:
        # Use yt-dlp to extract playlist info
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--dump-json',
            '--no-warnings',
            playlist_url
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            data = json.loads(line)
            videos.append({
                'video_id': data['id'],
                'title': data['title'],
                'url': f"https://youtube.com/watch?v={data['id']}"
            })
        
        return videos
    
    except Exception as e:
        logger.error(f"Failed to parse playlist: {e}")
        return []
```

**Integration in `prepare-job.sh`:**

```bash
# Check if URL is a playlist
if [[ "$MEDIA_FILE" =~ ^https?:// ]]; then
    # Check if playlist
    if [[ "$MEDIA_FILE" =~ playlist.*list= ]]; then
        log_info "📺 Playlist detected!"
        log_info "⬇️  Parsing playlist..."
        
        # Parse playlist
        PLAYLIST_INFO=$("$COMMON_VENV/bin/python3" -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')

from shared.online_downloader import get_playlist_videos

videos = get_playlist_videos('$MEDIA_FILE')
print(len(videos))
for video in videos:
    print(f\"{video['video_id']}|{video['title']}|{video['url']}\")
")
        
        # First line is count
        VIDEO_COUNT=$(echo "$PLAYLIST_INFO" | head -1)
        log_info "📋 Found $VIDEO_COUNT videos in playlist"
        
        # Ask user confirmation
        read -p "Process all $VIDEO_COUNT videos? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled by user"
            exit 0
        fi
        
        # Process each video
        JOB_IDS=()
        VIDEO_NUM=0
        
        while IFS='|' read -r video_id title url; do
            ((VIDEO_NUM++))
            
            log_info "Video $VIDEO_NUM/$VIDEO_COUNT: $title"
            
            # Create job for this video
            JOB_ID=$(./prepare-job.sh \
                --media "$url" \
                --workflow $WORKFLOW \
                --source-language $SOURCE_LANG \
                --target-language $TARGET_LANG \
                --silent | grep "Job created:" | awk '{print $3}')
            
            if [ -n "$JOB_ID" ]; then
                JOB_IDS+=("$JOB_ID")
                log_success "✅ Job created: $JOB_ID"
            else
                log_error "❌ Failed to create job for video $VIDEO_NUM"
            fi
        done < <(echo "$PLAYLIST_INFO" | tail -n +2)
        
        # Summary
        log_success "✅ Playlist complete: ${#JOB_IDS[@]} jobs created"
        log_info "📋 Job IDs:"
        for job_id in "${JOB_IDS[@]}"; do
            log_info "   - $job_id"
        done
        
        log_info ""
        log_info "Run all jobs:"
        for job_id in "${JOB_IDS[@]}"; do
            echo "  ./run-pipeline.sh -j $job_id"
        done
        
        exit 0
    fi
    
    # Single video (existing code)
    # ...
fi
```

---

## 📅 **Implementation Timeline**

### **Day 1 (4 hours)**
- ⏳ Feature 1: Real-time cost display
- ⏳ Test with existing jobs
- ⏳ Documentation

### **Day 2 (4 hours)**
- ⏳ Feature 2: Cost prediction module
- ⏳ Integration with prepare-job
- ⏳ Tests

### **Day 3 (8 hours)**
- ⏳ Feature 3: Playlist support
- ⏳ Batch job creation
- ⏳ Progress tracking
- ⏳ Tests + Documentation

**Total:** 16 hours (realistic with buffer)

---

## ✅ **Acceptance Criteria**

### **Feature 1: Real-Time Cost Display**
- ⏳ Show cost after each AI-using stage
- ⏳ Display running total
- ⏳ Show budget status
- ⏳ Warn at 80%/100% thresholds

### **Feature 2: Cost Prediction**
- ⏳ Estimate costs before execution
- ⏳ `--estimate-only` flag works
- ⏳ Accuracy within ±20%
- ⏳ Interactive confirmation

### **Feature 3: Playlist Support**
- ⏳ Detect playlist URLs
- ⏳ Parse all videos in playlist
- ⏳ Create job per video
- ⏳ Progress tracking
- ⏳ Batch execution summary

---

## 🎯 **Current Status**

**Today's Progress:**
- ✅ Week 3 Complete (YouTube Integration + Cost Tracking)
- ✅ ASR Path Bug Fixed
- ✅ 54/54 tests passing
- ✅ Week 4 plan created
- 📋 Ready to begin implementation

**Next Session:**
1. Implement Feature 1 (Real-time cost display)
2. Implement Feature 2 (Cost prediction)
3. Implement Feature 3 (Playlist support)
4. Tests + Documentation
5. Week 4 completion summary

---

## 📊 **Expected Outcomes**

**After Week 4:**
- ✅ **Phase 5 Progress:** 50% → 65% (+15%)
- ✅ **User Experience:** Dramatic improvement (cost visibility + playlists)
- ✅ **Production Features:** 6 major features complete
- ✅ **Test Coverage:** 70+ tests passing
- ✅ **Documentation:** Comprehensive guides

---

## 🚀 **Implementation Ready**

All code patterns documented above are:
- ✅ Architecturally sound
- ✅ Follow existing patterns
- ✅ Tested approach (similar to Week 3)
- ✅ Backward compatible
- ✅ Production ready design

**Ready to implement in next session!** 🎊
