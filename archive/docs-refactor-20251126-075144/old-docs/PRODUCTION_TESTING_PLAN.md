# Glossary System - Production Testing Plan

**Date**: November 26, 2025  
**Status**: Phase 1 & 2 Complete - Ready for Testing  
**Duration**: 1 week  
**Goal**: Validate implementation and measure quality improvements

---

## Testing Objectives

### Primary Goals:
1. ✅ Verify glossary system works end-to-end
2. 📊 Measure actual quality improvements
3. ⚡ Validate cache performance gains
4. 🐛 Identify any edge cases or bugs
5. 📈 Gather baseline metrics for future optimization

### Success Criteria:
- [ ] 3+ successful end-to-end pipeline runs
- [ ] Quality improvement of +15% or more measured
- [ ] Cache hit rate >80% on repeat films
- [ ] Zero critical bugs found
- [ ] All features working as documented

---

## Quick Start Guide

### Day 1: Baseline Test
```bash
# 1. Run baseline (without glossary)
./prepare-job.sh baseline "3 Idiots" 2009 hi en
./run-pipeline.sh baseline

# 2. Save baseline results
mkdir -p test-results/baseline/
cp in/baseline/subtitles/*.en.srt test-results/baseline/
```

### Day 2: Glossary Test
```bash
# 1. Enable glossary
cat > in/glossary-test/.glossary-test.env << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF

# 2. Run with glossary
./prepare-job.sh glossary-test "3 Idiots" 2009 hi en
./run-pipeline.sh glossary-test

# 3. Verify glossary loaded
cat in/glossary-test/03b_glossary_load/glossary_snapshot.json | jq '.glossary | length'
grep "bias terms" in/glossary-test/logs/pipeline.log
grep "Glossary applied" in/glossary-test/logs/pipeline.log
```

### Day 3: Cache Test
```bash
# Run same film again (should be faster)
./prepare-job.sh cache-test "3 Idiots" 2009 hi en
time ./run-pipeline.sh cache-test

# Check cache hit
grep "cache hit" in/cache-test/logs/pipeline.log
```

---

## Detailed Test Plan

### Week Schedule:

| Day | Focus | Est. Time |
|-----|-------|-----------|
| **Day 1** | Baseline testing | 2-3 hours |
| **Day 2** | Glossary validation | 2-3 hours |
| **Day 3** | Cache performance | 1-2 hours |
| **Day 4** | Quality measurement | 3-4 hours |
| **Day 5** | Edge cases | 2-3 hours |
| **Day 6** | Documentation | 2-3 hours |
| **Day 7** | Final review | 1-2 hours |

---

## Day 1: Baseline Testing

### Objective: Establish quality baseline

```bash
# 1. Prepare environment
mkdir -p test-results
cd /Users/rpatel/Projects/cp-whisperx-app

# 2. Run baseline test (NO glossary)
./prepare-job.sh baseline-3idiots "3 Idiots" 2009 hi en

# Disable glossary
echo "TMDB_ENRICHMENT_ENABLED=false" > in/baseline-3idiots/.baseline-3idiots.env

# 3. Run pipeline
time ./run-pipeline.sh baseline-3idiots

# 4. Save results
mkdir -p test-results/baseline/
cp -r in/baseline-3idiots/subtitles/*.srt test-results/baseline/
cp in/baseline-3idiots/logs/pipeline.log test-results/baseline/

# 5. Manual review
cat test-results/baseline/*.srt | head -100
```

**Expected Issues (Baseline)**:
- Character names misspelled
- Inconsistent Hinglish translations
- Generic terminology

---

## Day 2: Glossary Validation

### Objective: Verify glossary system works

```bash
# 1. Enable glossary
./prepare-job.sh glossary-3idiots "3 Idiots" 2009 hi en

cat > in/glossary-3idiots/.glossary-3idiots.env << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF

# 2. Run pipeline
time ./run-pipeline.sh glossary-3idiots

# 3. Verify glossary loaded
echo "=== Glossary Validation ==="
cat in/glossary-3idiots/03b_glossary_load/glossary_snapshot.json | jq '.glossary | length'
echo "Total terms loaded: $?"

# 4. Check ASR bias terms
grep "Using.*bias terms" in/glossary-3idiots/logs/pipeline.log

# 5. Check translation glossary
grep "Glossary applied" in/glossary-3idiots/logs/pipeline.log

# 6. Save results
mkdir -p test-results/glossary/
cp -r in/glossary-3idiots/subtitles/*.srt test-results/glossary/
cp in/glossary-3idiots/03b_glossary_load/glossary_snapshot.json test-results/glossary/
cp in/glossary-3idiots/logs/pipeline.log test-results/glossary/
```

**Validation Checklist**:
- [ ] Glossary snapshot created
- [ ] ASR bias terms used (check log)
- [ ] Translation glossary applied (check log)
- [ ] Subtitles generated successfully

---

## Day 3: Cache Performance

### Objective: Verify cache working and measure time savings

```bash
# 1. First run (cache miss) - already done in Day 2
echo "First run time:" > test-results/cache-timing.txt
grep "real" test-results/glossary/pipeline.log | tail -1 >> test-results/cache-timing.txt

# 2. Check cache created
ls -lah glossary/cache/tmdb/3-idiots_2009/
cat glossary/cache/tmdb/3-idiots_2009/metadata.json | jq .

# 3. Second run (cache hit)
./prepare-job.sh cache-3idiots "3 Idiots" 2009 hi en
cat > in/cache-3idiots/.cache-3idiots.env << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF

time ./run-pipeline.sh cache-3idiots 2>&1 | tee test-results/cache-run.log

# 4. Verify cache hit
grep "cache hit" in/cache-3idiots/logs/pipeline.log

# 5. Compare timings
echo "Second run time:" >> test-results/cache-timing.txt
grep "real" test-results/cache-run.log | tail -1 >> test-results/cache-timing.txt

cat test-results/cache-timing.txt
```

**Expected Results**:
- Cache directory created
- Second run significantly faster
- Cache hit logged

---

## Day 4: Quality Measurement

### Objective: Measure quality improvements

```bash
# 1. Compare subtitles
diff test-results/baseline/3_Idiots.en.srt test-results/glossary/3_Idiots.en.srt > test-results/quality-diff.txt

# 2. Count changes
CHANGES=$(grep -c "^<\|^>" test-results/quality-diff.txt)
echo "Changes detected: $CHANGES" > test-results/quality-report.txt

# 3. Manual quality review
cat > test-results/quality-checklist.txt << 'EOF'
Quality Checklist - 3 Idiots:

Character Names:
[ ] Rancho (Aamir Khan)
[ ] Farhan (R. Madhavan)
[ ] Raju (Sharman Joshi)
[ ] Virus (Boman Irani)

Hinglish Terms:
[ ] "yaar" - consistent translation
[ ] "matlab" - consistent translation
[ ] "bhai" - consistent translation

Film-Specific:
[ ] "ICE" (college name)
[ ] Technical terms

Overall Assessment:
[ ] Name accuracy improved: __%
[ ] Translation consistency improved: __%
[ ] No quality regressions
EOF

# 4. Sample comparison
echo "=== Sample Differences (First 50 lines) ===" > test-results/quality-samples.txt
head -50 test-results/quality-diff.txt >> test-results/quality-samples.txt
```

**Manual Review Required**: Review test-results/quality-samples.txt

---

## Day 5: Edge Cases

### Test 1: Film with No TMDB Data
```bash
./prepare-job.sh edge-nodata "Fake Film" 2099 hi en
./run-pipeline.sh edge-nodata

# Should complete successfully with master glossary only
echo $?  # Should be 0
```

### Test 2: Corrupted Cache
```bash
# Corrupt cache
echo "invalid" > glossary/cache/tmdb/3-idiots_2009/enrichment.json

# Run pipeline - should re-fetch
./prepare-job.sh edge-corrupt "3 Idiots" 2009 hi en
./run-pipeline.sh edge-corrupt

# Check logs for re-fetch
grep "re-fetch\|invalid" in/edge-corrupt/logs/pipeline.log
```

### Test 3: Missing Master Glossary
```bash
# Backup and remove
mv glossary/hinglish_master.tsv glossary/hinglish_master.tsv.backup

# Run pipeline - should degrade gracefully
./prepare-job.sh edge-missing "3 Idiots" 2009 hi en
./run-pipeline.sh edge-missing

# Restore
mv glossary/hinglish_master.tsv.backup glossary/hinglish_master.tsv
```

---

## Day 6: Documentation

### Create Test Report

```bash
cat > test-results/TEST_REPORT.md << 'EOF'
# Glossary System Production Test Report

**Date**: [Fill in]  
**Tester**: [Your name]  
**Status**: [PASS/FAIL]

## Summary

[Brief summary of testing]

## Results

### Functional Testing
- Glossary loading: [PASS/FAIL]
- ASR bias terms: [PASS/FAIL]
- Translation polish: [PASS/FAIL]
- Cache system: [PASS/FAIL]

### Quality Improvements
- Name accuracy: [+X%]
- Translation consistency: [+Y%]
- Overall: [+Z%]

### Cache Performance
- First run: [X seconds]
- Second run: [Y seconds]
- Time savings: [Z%]

### Edge Cases
- No TMDB data: [PASS/FAIL]
- Corrupted cache: [PASS/FAIL]
- Missing glossary: [PASS/FAIL]

## Issues Found

[List any issues]

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Decision

[GO / NO-GO / CONDITIONAL GO]

---
**Signature**: ___________________  
**Date**: ___________________
EOF
```

---

## Day 7: Final Review

### Go/No-Go Checklist

**Functional Requirements**:
- [ ] Glossary loads successfully
- [ ] ASR bias terms work
- [ ] Translation polish works
- [ ] Cache system functional

**Quality Requirements**:
- [ ] Quality improvement ≥15%
- [ ] No regressions
- [ ] Name accuracy improved

**Performance Requirements**:
- [ ] Cache hit rate >80%
- [ ] Time savings >50%

**Reliability Requirements**:
- [ ] Zero critical bugs
- [ ] Graceful error handling

### Decision Matrix

| Criteria | Weight | Score (/10) | Weighted |
|----------|--------|-------------|----------|
| Functional | 25% | | |
| Quality | 30% | | |
| Performance | 20% | | |
| Reliability | 15% | | |
| Documentation | 10% | | |
| **TOTAL** | 100% | | **/10** |

**Go Threshold**: ≥7.0/10

---

## Post-Testing Actions

### If GO:
```bash
# 1. Tag release
git tag -a v1.0-glossary -m "Glossary system production release"

# 2. Update documentation
# 3. Train team
# 4. Deploy to production
# 5. Monitor for 48 hours
```

### If NO-GO:
```bash
# 1. Document issues
# 2. Prioritize fixes
# 3. Schedule retest
# 4. Update stakeholders
```

---

## Quick Reference

### Essential Commands
```bash
# Run test
./run-pipeline.sh <job-id>

# Check glossary
cat in/<job-id>/03b_glossary_load/glossary_snapshot.json | jq .

# Check logs
grep "glossary\|bias terms" in/<job-id>/logs/pipeline.log

# Check cache
ls -lah glossary/cache/tmdb/
```

### Expected Log Messages
```
✓ Glossary system loaded successfully
  Total terms: XXX
Using XXX bias terms from glossary for ASR
✓ Glossary applied to XX segments
```

---

## Support

**Documentation**:
- `docs/GLOSSARY_SYSTEM_OPTIMIZATION.md` - Full design
- `docs/PHASE1_SESSION*_COMPLETE.md` - Implementation details
- `docs/GLOSSARY_IMPLEMENTATION_SUMMARY.md` - Overview

**Troubleshooting**:
- Check logs in `in/<job-id>/logs/pipeline.log`
- Verify configuration in `config/.env.pipeline`
- Check cache in `glossary/cache/tmdb/`

---

**Version**: 1.0  
**Last Updated**: November 26, 2025  
**Owner**: Development Team
