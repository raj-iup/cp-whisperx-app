# Quick Action Plan - Logging Architecture Implementation

**Date:** November 27, 2025  
**Goal:** Implement new logging architecture in all stages  
**Target:** 95% combined compliance (from current 50%)

---

## 🎯 UNDERSTANDING THE GAP

### Current Compliance: 50% (Below 80% Target)

**Breakdown:**
- ✅ **Original Standards: 91.7%** (StageIO, Logger, Config, Paths, Errors, Docs)
- ⚠️ **New Logging Arch: 0.0%** (Manifest tracking, I/O tracking, finalization)
- ⚠️ **Combined: 50.0%** (Need to reach 80%+)

**Why the gap?**
The new logging architecture standards (manifest tracking, dual logging, I/O tracking) were just defined on November 27, 2025 and haven't been implemented yet in existing stages.

**Bottom line:** Pipeline works great (91.7%), but needs quality enhancement.

---

## ⚡ QUICK START (1 Hour)

### Step 1: Review Templates (15 minutes)

Read these in order:
1. [LOGGING_QUICKREF.md](docs/LOGGING_QUICKREF.md) - Start here!
2. [DEVELOPER_STANDARDS.md](docs/DEVELOPER_STANDARDS.md) - Section 4.1 (Stage Template)
3. [demux implementation](scripts/run-pipeline.py) - Lines with StageIO in demux stage

### Step 2: Test Current Pipeline (15 minutes)

```bash
# Verify pipeline works
./test-glossary-quickstart.sh

# Check current logs
ls -la out/*/logs/
ls -la out/*/01_demux/
```

### Step 3: Complete Demux Stage (30 minutes)

The demux stage in `scripts/run-pipeline.py` already has partial implementation. Complete it:

```python
# Already there:
stage_io = StageIO("demux", self.job_dir, enable_manifest=True)
logger = stage_io.get_stage_logger()

# Add these (follow the pattern in run-pipeline.py lines 665-800):
stage_io.track_input(input_media, "video", format=input_media.suffix[1:])
stage_io.set_config({...})
stage_io.track_output(audio_output, "audio", ...)
stage_io.finalize(status="success", ...)
```

**Verify:**
```bash
# Run pipeline
./run-pipeline.sh translate <job-dir>

# Check files created
ls -la <job-dir>/01_demux/
# Should see: stage.log, manifest.json, audio.wav

# Validate manifest
jq . <job-dir>/01_demux/manifest.json
```

---

## 📅 PHASE-BY-PHASE PLAN

### Phase 1: PILOT ✈️ (Today - 1 hour) **START HERE**

**Goal:** Validate implementation pattern with one stage

**Tasks:**
1. ✅ Review logging architecture docs (done above)
2. 🔧 Complete demux stage in run-pipeline.py
3. ✅ Test and verify manifest creation
4. 📝 Document any issues/learnings

**Success Criteria:**
- [ ] Demux creates stage.log
- [ ] Demux creates manifest.json
- [ ] Manifest validates with `jq`
- [ ] Pipeline still runs successfully

**Time:** 1 hour  
**Compliance After:** ~55%

---

### Phase 2: CORE STAGES 🎯 (This Week - 4 hours)

**Goal:** Implement in high-value ML processing stages

**Stages (in order):**

#### 2.1 ASR Stage (1.5 hours) - **HIGHEST PRIORITY**
- File: `scripts/whisperx_asr.py`
- Why first: Most complex, most benefit from tracking
- Template: Section 4.1 in DEVELOPER_STANDARDS.md

**Add:**
```python
from shared.stage_utils import StageIO

stage_io = StageIO("asr", job_dir, enable_manifest=True)
logger = stage_io.get_stage_logger("DEBUG" if debug else "INFO")

# Track audio input
stage_io.track_input(audio_file, "audio", format="wav")

# Track configuration
stage_io.set_config({
    "model": whisper_model,
    "device": device,
    "batch_size": batch_size,
    "language": language
})

# Track output
stage_io.track_output(segments_file, "transcript", 
                      format="json",
                      segments=len(segments))

# Track model cache (if exists)
if model_cache.exists():
    stage_io.track_intermediate(model_cache,
                                retained=True,
                                reason="Model weights cache")

# Finalize
stage_io.finalize(status="success", 
                 segments_count=len(segments),
                 throughput_realtime=duration_ratio)
```

#### 2.2 Alignment Stage (1.5 hours)
- File: `scripts/mlx_alignment.py`
- Template: Same as ASR
- Track: input segments, aligned segments, config

#### 2.3 Translation Stage (1 hour)
- File: `scripts/translation_stage.py` (if exists) or in run-pipeline.py
- Track: input transcript, translated output, language pairs

**Success Criteria:**
- [ ] All 3 stages create manifests
- [ ] Data lineage traceable (output → next input)
- [ ] No pipeline errors
- [ ] Logs show proper dual logging

**Time:** 4 hours total  
**Compliance After:** ~70%

---

### Phase 3: REMAINING STAGES 📦 (Next Week - 4 hours)

**Goal:** Complete all remaining stages

**Stages (batch process):**

#### 3.1 Preprocessing Stages (1.5 hours)
- TMDB Enrichment (`scripts/tmdb_enrichment_stage.py`)
- Glossary Load (`scripts/glossary_builder.py`)
- Source Separation (`scripts/source_separation.py`)

#### 3.2 Detection Stages (1 hour)
- PyAnnote VAD (`scripts/pyannote_vad.py`)
- Lyrics Detection (`scripts/lyrics_detection.py`)

#### 3.3 Output Stages (1.5 hours)
- Subtitle Generation (`scripts/subtitle_gen.py`)
- Mux (`scripts/mux.py`)

**Pattern for Each:**
1. Copy template from LOGGING_QUICKREF.md
2. Identify inputs/outputs for stage
3. Add tracking calls
4. Add finalization
5. Test individually

**Success Criteria:**
- [ ] All 10 stages have manifests
- [ ] Full pipeline run creates all logs
- [ ] Data lineage complete
- [ ] Combined compliance ≥ 95%

**Time:** 4 hours total  
**Compliance After:** ~95%

---

### Phase 4: VALIDATION & CLEANUP 🧹 (1 hour)

**Goal:** Verify everything works together

**Tasks:**
1. Run full pipeline end-to-end
2. Validate all manifests created
3. Check data lineage integrity
4. Update compliance report
5. Document any edge cases

**Validation Script:**
```bash
#!/bin/bash
# validate_logging.sh

JOB_DIR="$1"

echo "Validating logging architecture..."

# Check main pipeline log
if [ -f "$JOB_DIR/logs/99_pipeline_"*.log ]; then
    echo "✓ Main pipeline log exists"
else
    echo "✗ Main pipeline log missing"
fi

# Check each stage
for stage_dir in "$JOB_DIR"/[0-9]*_*/; do
    stage=$(basename "$stage_dir")
    
    if [ -f "$stage_dir/stage.log" ]; then
        echo "✓ $stage: stage.log"
    else
        echo "✗ $stage: stage.log missing"
    fi
    
    if [ -f "$stage_dir/manifest.json" ]; then
        # Validate JSON
        if jq . "$stage_dir/manifest.json" > /dev/null 2>&1; then
            echo "✓ $stage: manifest.json valid"
        else
            echo "✗ $stage: manifest.json invalid"
        fi
    else
        echo "✗ $stage: manifest.json missing"
    fi
done

echo "Done!"
```

**Time:** 1 hour  
**Final Compliance:** 95%+ ✅

---

## 📋 DAILY CHECKLIST

### Day 1 (Today) - PILOT
- [ ] Read LOGGING_QUICKREF.md (15 min)
- [ ] Review demux implementation in run-pipeline.py (15 min)
- [ ] Complete demux stage logging (20 min)
- [ ] Test and verify (10 min)
- [ ] Document learnings (10 min)

**End of Day:** 55% compliance

### Day 2-3 (This Week) - CORE STAGES
- [ ] Implement ASR stage (1.5 hours)
- [ ] Test ASR stage individually
- [ ] Implement Alignment stage (1.5 hours)
- [ ] Test Alignment stage individually
- [ ] Implement Translation stage (1 hour)
- [ ] Test full pipeline with 4 stages

**End of Day 3:** 70% compliance

### Day 4-5 (Next Week) - REMAINING STAGES
- [ ] Batch implement preprocessing stages (1.5 hours)
- [ ] Batch implement detection stages (1 hour)
- [ ] Batch implement output stages (1.5 hours)
- [ ] Integration testing (1 hour)

**End of Day 5:** 95% compliance ✅

---

## 🚨 COMMON PITFALLS & SOLUTIONS

### Pitfall 1: Forgot to finalize()
**Symptom:** Manifest not created or status shows "running"  
**Solution:** Always call `stage_io.finalize()` before every return

### Pitfall 2: Wrong file paths in manifest
**Symptom:** Data lineage broken, next stage can't find input  
**Solution:** Use `stage_io.get_input_path()` and `stage_io.get_output_path()`

### Pitfall 3: Manifest JSON invalid
**Symptom:** `jq` fails to parse manifest.json  
**Solution:** Check for unquoted strings, trailing commas

### Pitfall 4: Logging to wrong logger
**Symptom:** DEBUG messages in pipeline log  
**Solution:** Use `logger.debug()` (stage only), `self.logger.info()` (pipeline)

### Pitfall 5: Missing intermediate files
**Symptom:** Cache files not documented  
**Solution:** Track ALL files created, even temporary ones

---

## 🎯 SUCCESS METRICS

### By End of Week
- ✅ 4 stages with full logging (demux, ASR, alignment, translation)
- ✅ 70%+ combined compliance
- ✅ Data lineage traceable for core workflow
- ✅ No pipeline regressions

### By End of Next Week
- ✅ All 10 stages with full logging
- ✅ 95%+ combined compliance
- ✅ Complete data lineage documentation
- ✅ Validation scripts working

---

## 📞 GET HELP

### Quick Reference
- [LOGGING_QUICKREF.md](docs/LOGGING_QUICKREF.md) - All patterns

### Complete Guide
- [LOGGING_ARCHITECTURE.md](docs/LOGGING_ARCHITECTURE.md) - Full architecture

### Visual Guide
- [LOGGING_DIAGRAM.md](docs/LOGGING_DIAGRAM.md) - Diagrams and flows

### Templates
- [DEVELOPER_STANDARDS.md](docs/DEVELOPER_STANDARDS.md) - Section 4.1

### Questions?
- Check "Common Pitfalls" section above
- Review manifest schema in LOGGING_ARCHITECTURE.md
- Refer to demux stage implementation as example

---

## 🎉 MILESTONES

### Milestone 1: Pilot Complete ✈️
- **Target:** 1 stage (demux)
- **Time:** 1 hour
- **Compliance:** 55%
- **Deliverable:** Working manifest example

### Milestone 2: Core Complete 🎯
- **Target:** 4 stages total
- **Time:** 5 hours cumulative
- **Compliance:** 70%
- **Deliverable:** ML pipeline fully tracked

### Milestone 3: Full Implementation 📦
- **Target:** All 10 stages
- **Time:** 9 hours cumulative
- **Compliance:** 95%
- **Deliverable:** Complete data lineage

### Milestone 4: Production Ready 🚀
- **Target:** Validated + documented
- **Time:** 10 hours cumulative
- **Compliance:** 95%+ ✅
- **Deliverable:** Audit-ready pipeline

---

**Start Now:** Phase 1 - Pilot (demux stage) - 1 hour  
**Reference:** [LOGGING_QUICKREF.md](docs/LOGGING_QUICKREF.md)  
**Template:** Section 4.1 in [DEVELOPER_STANDARDS.md](docs/DEVELOPER_STANDARDS.md)

**YOU CAN DO THIS! 🚀**
