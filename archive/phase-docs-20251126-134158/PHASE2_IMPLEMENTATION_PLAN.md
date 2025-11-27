# Phase 2: ASR Optimization Implementation Plan

**Date**: November 26, 2024  
**Duration**: 2-3 days  
**Expected Improvement**: Additional 15% accuracy (85-90% → 90-93%)

---

## Overview

Phase 2 focuses on Tier 2 improvements from the ASR analysis:
1. Two-step transcription workflow (hi→hi then hi→en)
2. Anti-hallucination configuration tuning
3. Glossary learning and enhancement

## Task Breakdown

### Task 1: Two-Step Transcription Workflow

**Current Behavior**: Single-pass transcription directly to target language  
**Proposed**: Transcribe in source language first, then translate separately  
**Benefit**: Better accuracy by separating transcription and translation concerns

#### Implementation Steps:

1. **Add workflow configuration option**
   - Add `TWO_STEP_TRANSCRIPTION` flag to job config
   - Default: `false` (maintain backward compatibility)
   - When `true`: Run hi→hi transcription, then translate

2. **Modify ASR stage**
   - Check workflow configuration
   - If two-step enabled: Force source language transcription
   - Output: Clean Hindi transcript

3. **Enhance translation stage**
   - Accept pre-transcribed Hindi segments
   - Apply IndicTrans2 with full context
   - Better leverage glossary terms

4. **Update pipeline orchestration**
   - Detect two-step mode from job config
   - Insert explicit translation step after ASR
   - Maintain timing and metadata

**Files to Modify**:
- `scripts/prepare-job.py` - Add two-step option
- `scripts/06_asr/transcribe.py` - Add source-only mode
- `scripts/10_translation/translate.py` - Enhance input handling
- `run-pipeline.sh` - Add two-step workflow detection

**Testing**:
```bash
./prepare-job.sh \
  --media 'in/Jaane Tu Ya Jaane Na 2008.mp4' \
  --workflow translate \
  --source-language hi \
  --target-language en \
  --two-step \
  --start-time 00:10:00 \
  --end-time 00:15:00
```

---

### Task 2: Anti-Hallucination Configuration

**Current Issues**:
- Temperature too high (allows hallucinations)
- Compression ratio threshold too lenient
- No speech threshold needs tuning

#### Parameter Tuning:

**Current Values** (from test_phase1.sh):
```bash
WHISPER_TEMPERATURE=0.0,0.1,0.2
WHISPER_BEAM_SIZE=8
WHISPER_BEST_OF=8
WHISPER_NO_SPEECH_THRESHOLD=0.7
WHISPER_LOGPROB_THRESHOLD=-0.5
WHISPER_COMPRESSION_RATIO_THRESHOLD=2.0
```

**Proposed Phase 2 Values**:
```bash
# Stricter hallucination prevention
WHISPER_TEMPERATURE=0.0          # Single value, no sampling
WHISPER_BEAM_SIZE=10             # More thorough search
WHISPER_BEST_OF=10               # More candidates
WHISPER_NO_SPEECH_THRESHOLD=0.8  # Higher threshold (was 0.7)
WHISPER_LOGPROB_THRESHOLD=-0.4   # Stricter confidence (was -0.5)
WHISPER_COMPRESSION_RATIO_THRESHOLD=1.8  # Detect repetition (was 2.0)

# Additional anti-hallucination
WHISPER_CONDITION_ON_PREVIOUS_TEXT=false  # Reduce context dependency
WHISPER_REPETITION_PENALTY=1.2   # NEW: Penalize repetitions
```

**Implementation**:
1. Update `config/pipeline.conf` with new defaults
2. Add configuration validation
3. Document parameter rationale

**Files to Modify**:
- `config/pipeline.conf` - Update defaults
- `scripts/shared/config.py` - Add new parameters
- `docs/user-guide/configuration.md` - Document changes

---

### Task 3: Glossary Enhancement

**Current State**: 117 static terms (75 master + 42 TMDB)  
**Proposed**: Dynamic glossary learning from transcription errors

#### Sub-tasks:

**3.1: Glossary Learning from Transcription**
- Detect character names in transcripts
- Compare with TMDB glossary
- Identify missing terms
- Auto-add to job-specific glossary

**3.2: Context-Aware Glossary Application**
- Apply glossary based on speaker context
- Use diarization info to boost character names
- Time-based glossary windows (30s)

**3.3: Glossary Quality Metrics**
- Track glossary term usage
- Measure term hit rate
- Identify ineffective terms
- Suggest term improvements

#### Implementation:

**New Script**: `scripts/03_glossary_load/glossary_learner.py`
```python
class GlossaryLearner:
    def extract_potential_terms(self, transcript):
        """Extract named entities from transcript"""
        
    def compare_with_tmdb(self, entities, tmdb_cast):
        """Find missing character names"""
        
    def generate_job_glossary(self, missing_terms):
        """Create job-specific glossary additions"""
        
    def update_master_glossary(self, validated_terms):
        """Add validated terms to master glossary"""
```

**Files to Create**:
- `scripts/03_glossary_load/glossary_learner.py` - Learning logic
- `scripts/03_glossary_load/glossary_validator.py` - Term validation

**Files to Modify**:
- `scripts/03_glossary_load/load_glossary.py` - Integrate learner
- `scripts/06_asr/transcribe.py` - Use job glossary

---

## Implementation Priority

### Week 1 (Days 1-3)
- ✅ Phase 1 complete (MPS + hybrid bias)
- 🔧 Task 2: Anti-hallucination tuning (4 hours)
  - Update configuration files
  - Test with dialogue scenes
  - Validate improvements

### Week 1 (Days 4-5)
- 🔧 Task 1: Two-step transcription (8 hours)
  - Implement workflow flag
  - Modify ASR stage
  - Test end-to-end

### Week 2 (Days 1-2)
- 🔧 Task 3: Glossary enhancement (8 hours)
  - Implement learner
  - Integrate with pipeline
  - Test and validate

### Week 2 (Day 3)
- ✅ Testing and validation
- 📊 Performance measurement
- 📝 Documentation updates

---

## Success Criteria

### Task 1: Two-Step Transcription
- ✅ Clean Hindi transcript generated
- ✅ Translation quality improved by 5-10%
- ✅ Character names more accurate
- ✅ Backward compatible (no breaking changes)

### Task 2: Anti-Hallucination
- ✅ Hallucination rate reduced by 50%
- ✅ No accuracy degradation on clean speech
- ✅ Repetition detection improved
- ✅ Configurable and documented

### Task 3: Glossary Enhancement
- ✅ Auto-detected character names
- ✅ Job-specific glossary generation
- ✅ Term hit rate >60%
- ✅ Integration with existing glossary system

---

## Testing Strategy

### Test Scenarios

**Scenario 1: Clean Dialogue Scene**
```bash
# Time: 10:00-15:00 (5 minutes of dialogue)
./prepare-job.sh --media 'in/Jaane Tu Ya Jaane Na 2008.mp4' \
  --workflow translate --source-language hi --target-language en \
  --start-time 00:10:00 --end-time 00:15:00 --two-step
```
Expected: High accuracy, minimal hallucinations

**Scenario 2: Music/Dialogue Mix**
```bash
# Time: 0:00-10:00 (song + dialogue)
./prepare-job.sh --media 'in/Jaane Tu Ya Jaane Na 2008.mp4' \
  --workflow translate --source-language hi --target-language en \
  --start-time 00:00:00 --end-time 00:10:00 --two-step
```
Expected: Lyrics filtered, dialogue accurate

**Scenario 3: Character Name Heavy**
```bash
# Scene with multiple character interactions
./prepare-job.sh --media 'in/Jaane Tu Ya Jaane Na 2008.mp4' \
  --workflow translate --source-language hi --target-language en \
  --start-time 00:20:00 --end-time 00:25:00 --two-step
```
Expected: Character names correctly identified and preserved

### Validation Metrics

**Transcription Quality**:
- Word Error Rate (WER) < 10%
- Character Recognition Rate (CRR) > 90%
- Hallucination Rate < 5%

**Translation Quality**:
- BLEU score > 40
- Glossary term usage > 60%
- No untranslated Hindi words in English subtitles

**Performance**:
- Processing time < 2x realtime (10 min for 5 min clip)
- Memory usage < 4GB
- GPU utilization > 70%

---

## Configuration Files

### Updated pipeline.conf
```ini
# ============================================================================
# Phase 2: Anti-Hallucination Configuration
# ============================================================================

[transcription]
model_name=large-v3
compute_type=float16
device=mps

# Phase 2: Stricter hallucination prevention
temperature=0.0
beam_size=10
best_of=10
no_speech_threshold=0.8
logprob_threshold=-0.4
compression_ratio_threshold=1.8
condition_on_previous_text=false
repetition_penalty=1.2

# Two-step workflow
two_step_transcription=false  # Enable with --two-step flag

[bias]
strategy=hybrid
window_seconds=30
stride_seconds=10
topk=15

# Phase 2: Glossary learning
enable_glossary_learning=true
auto_add_character_names=true
glossary_confidence_threshold=0.7
```

---

## Rollback Plan

If Phase 2 causes issues:

1. **Revert configuration**:
   ```bash
   git checkout config/pipeline.conf
   ```

2. **Disable two-step mode**:
   - Set `two_step_transcription=false` in config
   - Or omit `--two-step` flag

3. **Restore Phase 1 parameters**:
   ```bash
   WHISPER_TEMPERATURE=0.0,0.1,0.2
   WHISPER_BEAM_SIZE=8
   WHISPER_BEST_OF=8
   ```

4. **Fallback command**:
   ```bash
   ./prepare-job.sh --media file.mp4 --workflow translate \
     --source-language hi --target-language en \
     # No --two-step flag = Phase 1 behavior
   ```

---

## Documentation Updates

Files to update:
- `docs/user-guide/workflows.md` - Add two-step workflow
- `docs/user-guide/configuration.md` - Document new parameters
- `docs/technical/pipeline.md` - Explain two-step architecture
- `PHASE2_COMPLETE.md` - Implementation summary

---

## Next Steps

After Phase 2 completion:
- Measure actual improvements vs. expectations
- Collect metrics for Phase 3 planning
- Update ASR analysis with Phase 2 results
- Plan Phase 3 implementation (multi-pass refinement)

---

**Status**: Ready for implementation  
**Estimated Effort**: 20-24 hours over 1 week  
**Expected Outcome**: 90-93% accuracy, improved glossary system
