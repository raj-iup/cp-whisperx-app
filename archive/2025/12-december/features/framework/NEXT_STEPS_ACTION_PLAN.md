# Next Steps - Action Plan

**Date:** 2025-12-08 15:30 UTC  
**Status:** ✅ Framework Complete | 🔄 Pipeline Running | 🎯 Ready for Cache Integration

---

## 🎉 Completed This Session

### 1. BRD/TRD Framework ✅
- Created `docs/brd/` and `docs/trd/` directories
- Created BRD and TRD templates
- Created master index (`docs/brd/INDEX.md`)
- Backfilled 6 BRDs for AD-009 through AD-014

### 2. Pipeline Started ✅
- Job: `job-20251208-rpatel-0004`
- Workflow: Transcribe
- Media: `in/Energy Demand in AI.mp4`
- Status: Running (ASR stage with MLX)
- Purpose: Generate baseline for AD-014 testing

---

## 🔄 Current Pipeline Status

**Pipeline:** Running at Stage 06 (ASR)
- Started: 08:26:31
- Current: 08:33:00 (running ASR with MLX backend)
- Expected ASR time: 5-15 minutes
- Expected total time: 10-20 minutes

**Monitor:**
```bash
tail -f out/2025/12/08/rpatel/4/99_pipeline_*.log
```

---

## 🎯 Next Steps (Priority Order)

### Immediate (While Pipeline Runs)

**1. Monitor Pipeline Completion (5-15 min)**
```bash
# Watch pipeline progress
tail -f out/2025/12/08/rpatel/4/99_pipeline_*.log

# Or check status periodically
tail -n 20 out/2025/12/08/rpatel/4/99_pipeline_*.log
```

**Expected Output:**
- ✅ Stage demux: COMPLETED
- ✅ Stage source_separation: COMPLETED (347s)
- ✅ Stage pyannote_vad: COMPLETED (40s)
- 🔄 Stage asr: RUNNING (MLX backend)
- ⏳ Stage alignment: PENDING
- ⏳ Pipeline completion

---

### After Pipeline Completes

**2. Integrate Caching into run-pipeline.py (2-4 hours)**

**Goal:** Enable baseline cache check/load/store

**Implementation:**
```python
# In run-pipeline.py, before ASR stage

from shared.media_identity import compute_media_id
from shared.cache_manager import MediaCacheManager

# Compute media ID
media_file = Path(input_media)
media_id = compute_media_id(media_file)
logger.info(f"Media ID: {media_id}")

# Check for cached baseline
cache_mgr = MediaCacheManager()
if workflow == "subtitle" and cache_mgr.has_baseline(media_id):
    logger.info("✅ Found cached baseline! Skipping ASR/alignment...")
    baseline = cache_mgr.get_baseline(media_id)
    
    # Copy cached files to job directories
    # Skip stages 04-07 (source_sep, vad, asr, alignment)
    # Start from stage 08 (lyrics detection)
    
else:
    logger.info("No cached baseline found. Running full ASR/alignment...")
    # Run normal pipeline
    # After alignment completes, store baseline
    cache_mgr.store_baseline(media_id, {
        'asr_results': asr_results,
        'aligned_segments': aligned_segments,
        'glossary': glossary_data,
        'media_metadata': metadata
    })
```

**Tasks:**
- [ ] Add baseline check logic before stage 04
- [ ] Add baseline load logic if cache hit
- [ ] Add baseline store logic after stage 07
- [ ] Handle cache miss gracefully
- [ ] Add logging for cache hit/miss

**Testing:**
```bash
# First run (no cache)
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe
./run-pipeline.sh out/2025/12/08/rpatel/4

# Second run (with cache) - should be 70-80% faster
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe
./run-pipeline.sh out/2025/12/08/rpatel/5
```

---

**3. Create TRD Documents (20-30 min)**

**Priority: TRD-014 first, then others**

Create technical requirement documents matching the BRDs:
- [ ] `docs/trd/TRD-014.md` - Multi-phase subtitle workflow (highest priority)
- [ ] `docs/trd/TRD-009.md` - Quality-first development standards
- [ ] `docs/trd/TRD-010.md` - Workflow output implementation
- [ ] `docs/trd/TRD-011.md` - File path validation framework
- [ ] `docs/trd/TRD-012.md` - Log path helper functions
- [ ] `docs/trd/TRD-013.md` - Test directory organization

**Use template:** `docs/trd/TRD_TEMPLATE.md`

---

**4. Run Performance Validation (1-2 hours)**

**Goal:** Measure actual speedup from caching

**Test Plan:**
```bash
# Test 1: First run (baseline generation)
time ./run-pipeline.sh out/2025/12/08/rpatel/job1
# Expected: 10-20 minutes (full pipeline)

# Test 2: Second run (baseline cached)
time ./run-pipeline.sh out/2025/12/08/rpatel/job2
# Expected: 2-4 minutes (70-80% reduction)

# Test 3: Validate quality
compare_quality job1 job2
# Expected: Identical ASR/alignment quality
```

**Metrics to Measure:**
- [ ] First run time (baseline)
- [ ] Second run time (cached)
- [ ] Speedup percentage
- [ ] ASR quality (WER comparison)
- [ ] Alignment quality (word timestamp accuracy)

**Document Results:**
- Update `AD014_WEEK1_COMPLETE_SUMMARY.md`
- Create performance validation report
- Update `IMPLEMENTATION_TRACKER.md`

---

**5. Test with Bollywood Media (Optional - 1 hour)**

**Goal:** Validate cache with subtitle workflow

```bash
# First run: Generate baseline + subtitles
./prepare-job.sh \
  --media "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu

time ./run-pipeline.sh out/2025/12/08/rpatel/job3
# Expected: 20-40 minutes (full subtitle pipeline)

# Second run: Add more languages using cached baseline
./prepare-job.sh \
  --media "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --workflow subtitle \
  --source-language hi \
  --target-languages es,ru,zh,ar

time ./run-pipeline.sh out/2025/12/08/rpatel/job4
# Expected: 5-10 minutes (reuses cached ASR/alignment)
```

---

## 📊 Success Criteria

### Framework Success ✅
- [x] BRD/TRD directories created
- [x] Templates available
- [x] 6 BRDs backfilled (AD-009 through AD-014)
- [x] Master index tracking document
- [ ] 6 TRDs created (matches BRDs)

### AD-014 Week 1 Success
- [x] Day 1-2: Foundation (media_identity, cache_manager)
- [ ] Day 3-4: Cache integration (CURRENT)
  - [ ] Integrate into run-pipeline.py
  - [ ] Test first run (generate baseline)
  - [ ] Test second run (load baseline)
  - [ ] Measure speedup (target: 70-80%)
- [ ] Day 5: Performance validation
  - [ ] First vs second run comparison
  - [ ] Quality metrics validation
  - [ ] Documentation updates

---

## 📋 Implementation Checklist

### Today (Cache Integration)
- [ ] Monitor pipeline completion
- [ ] Review run-pipeline.py integration points
- [ ] Add baseline check before ASR
- [ ] Add baseline load on cache hit
- [ ] Add baseline store after alignment
- [ ] Test with transcribe workflow (Energy Demand)
- [ ] Measure performance improvement

### Tomorrow (Performance Validation)
- [ ] Run first baseline generation
- [ ] Run second with cache (same media)
- [ ] Compare times (expect 70-80% reduction)
- [ ] Validate quality metrics unchanged
- [ ] Document results

### This Week (Complete Week 1)
- [ ] Create all TRD documents
- [ ] Update AD014_WEEK1_COMPLETE_SUMMARY.md
- [ ] Update IMPLEMENTATION_TRACKER.md
- [ ] Prepare for Week 2 (advanced features)

---

## 🔗 Quick Links

**Framework:**
- [BRD Index](docs/brd/INDEX.md) - Master tracking
- [BRD Template](docs/brd/BRD_TEMPLATE.md) - For new BRDs
- [TRD Template](docs/trd/TRD_TEMPLATE.md) - For new TRDs

**Current Work:**
- [BRD-014](docs/brd/BRD-014.md) - Multi-phase subtitle workflow
- [AD014 Summary](AD014_WEEK1_COMPLETE_SUMMARY.md) - Week 1 progress
- [AD014 Quick Reference](AD014_QUICK_REFERENCE.md) - Code patterns

**Implementation:**
- [shared/media_identity.py](shared/media_identity.py) - Media ID computation
- [shared/cache_manager.py](shared/cache_manager.py) - Cache management
- [run-pipeline.py](run-pipeline.py) - Pipeline orchestration (needs integration)

**Documentation:**
- [Architecture](docs/ARCHITECTURE.md) - All ADs
- [Developer Standards](docs/developer/DEVELOPER_STANDARDS.md) - Coding standards
- [Copilot Instructions](.github/copilot-instructions.md) - Development guide

---

## 💡 Pro Tips

**Monitoring Pipeline:**
```bash
# Watch live
tail -f out/2025/12/08/rpatel/4/99_pipeline_*.log

# Check last 20 lines
tail -n 20 out/2025/12/08/rpatel/4/99_pipeline_*.log

# Check completion
ls -lh out/2025/12/08/rpatel/4/07_alignment/
```

**Testing Cache:**
```bash
# Check if baseline stored
ls -lh ~/.cp-whisperx/cache/baselines/

# Verify media ID computation
python3 -c "
from pathlib import Path
from shared.media_identity import compute_media_id
media_id = compute_media_id(Path('in/Energy Demand in AI.mp4'))
print(f'Media ID: {media_id}')
"
```

**Performance Comparison:**
```bash
# Time first run
time ./run-pipeline.sh job1

# Time second run
time ./run-pipeline.sh job2

# Calculate speedup
python3 -c "
first = 600  # seconds
second = 120  # seconds
speedup = (first - second) / first * 100
print(f'Speedup: {speedup:.1f}%')
"
```

---

**Status:** ✅ Framework Complete | 🔄 Pipeline Running | 🎯 Ready for Cache Integration

**Next Action:** Monitor pipeline, then integrate caching into run-pipeline.py
