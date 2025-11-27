# Glossary System - Quick Reference

## TL;DR

**Status**: Good foundation, needs consolidation & integration  
**Quick Win**: Run `python3 tools/merge_glossaries.py` (30 min)  
**Full Fix**: 11 hours over 4 weeks  
**Expected ROI**: 30-50% better translation quality  

---

## Current Situation

### What We Have ✅
- 55 manual terms (high quality)
- 115 auto-generated terms
- 19 detailed film prompts
- Advanced selection algorithms
- Pipeline stage (Stage 11)

### What's Broken ❌
- Multiple incompatible glossaries
- Not used in translation
- Not applied to subtitles
- No learning from usage

---

## The Problem

```
┌──────────────────────┐
│  Master Glossary     │  55 terms, manual, good
│  (hinglish_master)   │
└──────────────────────┘
         ⊥ (not connected)

┌──────────────────────┐
│  Cache Glossary      │  115 terms, auto, different format
│  (satte-pe-satta)    │
└──────────────────────┘
         ⊥ (not connected)

┌──────────────────────┐
│  Pipeline Stages     │  Doesn't use either glossary!
│  (translation,subs)  │
└──────────────────────┘
```

---

## The Solution

### Phase 1: Consolidate (2 hours)
```
Master + Cache → Unified Glossary (170+ terms)
```

### Phase 2: Integrate (3 hours)
```
Translation Stage → Use glossary
Glossary Applier  → New stage
Subtitle Gen      → Apply glossary
```

### Phase 3: Enhance (4 hours)
```
Context-aware selection
Film-specific rules
Learning from usage
```

---

## Quick Start

### 1. Merge Glossaries (30 min)
```bash
cd /Users/rpatel/Projects/cp-whisperx-app
python3 tools/merge_glossaries.py
```

**Output**: `glossary/unified_glossary.tsv` (170+ terms)

### 2. Check Result
```bash
head -20 glossary/unified_glossary.tsv
wc -l glossary/unified_glossary.tsv
```

### 3. Next Steps
See `docs/GLOSSARY_SUMMARY.md` for implementation plan

---

## Documentation

### For Quick Win
📄 **GLOSSARY_QUICKWIN_MERGE.md**
- How to merge glossaries
- Expected results
- Troubleshooting

### For Full Analysis
📄 **GLOSSARY_ANALYSIS_STRATEGY.md** (18KB)
- Complete analysis
- 4-phase implementation plan
- Architecture diagrams
- Success metrics

### For Summary
📄 **GLOSSARY_SUMMARY.md** (8KB)
- Executive summary
- Problems & solutions
- Timeline & ROI

---

## File Structure

### Current
```
glossary/
├── hinglish_master.tsv     # 55 manual terms
├── cache/
│   └── satte-pe-satta.tsv  # 115 auto terms
├── prompts/                 # 19 film prompts
│   ├── 3_idiots_2009.txt
│   └── ...
└── glossary_learned/        # Empty (unused)
```

### After Merge
```
glossary/
├── unified_glossary.tsv    # ✨ 170+ terms, single format
├── hinglish_master.tsv     # (keep as backup)
├── cache/                   # (keep as backup)
└── prompts/                 # (will use in Phase 3)
```

---

## Impact Examples

### Before (No Glossary)
```
"Hey yaar, kya scene hai?"
→ "Hey friend, what's the matter?"
```
❌ Generic, unnatural

### After (With Glossary)
```
"Hey yaar, kya scene hai?"
→ "Hey dude, what's up?"
```
✅ Natural, contextual

### Film-Specific (3 Idiots)
```
"All is well, yaar"
→ "All is well, dude"
```
✅ Keeps sacred phrase

---

## Timeline

### Week 1: Consolidation ✅ START HERE
- Merge glossaries
- Create unified format
- Validate data

### Week 2: Integration 🎯
- Update translation stage
- Create glossary applier
- Test pipeline

### Week 3: Enhancement 📈
- Context-aware selection
- Film-specific rules
- Learning system

### Week 4: Quality 🔧
- Validation tools
- Automated tests
- Documentation

---

## Success Metrics

### Phase 1 Target
- ✅ Single unified glossary
- ✅ 170+ terms
- ✅ Consistent format

### Phase 2 Target
- ✅ 80%+ term coverage in translations
- ✅ Glossary actively used
- ✅ Measurable improvement

### Phase 3 Target
- ✅ 90%+ term accuracy
- ✅ Context-aware selection
- ✅ Learning from usage

---

## Tools & Scripts

### Merge Glossaries
```bash
tools/merge_glossaries.py
```
- Combines all glossaries
- Validates format
- Reports statistics

### Validate Glossary (Future)
```bash
tools/validate_glossary.py
```
- Check format
- Find duplicates
- Validate confidence

### Glossary Dashboard (Future)
```bash
tools/glossary_dashboard.py
```
- Usage statistics
- Coverage metrics
- Quality reports

---

## Key Files

### Implementation
- `shared/glossary.py` - Basic glossary class
- `shared/glossary_advanced.py` - Advanced strategies
- `scripts/glossary_builder.py` - Stage 11

### Documentation
- `docs/GLOSSARY_README.md` - This file (quick ref)
- `docs/GLOSSARY_SUMMARY.md` - Executive summary
- `docs/GLOSSARY_ANALYSIS_STRATEGY.md` - Full analysis
- `docs/GLOSSARY_QUICKWIN_MERGE.md` - Merge guide

### Tools
- `tools/merge_glossaries.py` - Merge script

---

## Quick Commands

```bash
# Merge glossaries
python3 tools/merge_glossaries.py

# Check result
head -20 glossary/unified_glossary.tsv

# Count terms
wc -l glossary/unified_glossary.tsv

# View master
cat glossary/hinglish_master.tsv

# View prompt
cat glossary/prompts/3_idiots_2009.txt

# Run glossary builder
OUTPUT_DIR=out/<job> python3 scripts/glossary_builder.py
```

---

## Need Help?

### Quick Win
1. Read `GLOSSARY_QUICKWIN_MERGE.md`
2. Run `python3 tools/merge_glossaries.py`
3. Done!

### Full Implementation
1. Read `GLOSSARY_SUMMARY.md`
2. Read `GLOSSARY_ANALYSIS_STRATEGY.md`
3. Follow 4-phase plan

### Troubleshooting
- Merge fails? Check TSV format
- Terms missing? Check source files
- Integration broken? Check stage order

---

## Status Checklist

### Phase 1: Consolidation
- [ ] Run merge script
- [ ] Verify unified glossary
- [ ] Backup original files
- [ ] Update documentation

### Phase 2: Integration
- [ ] Update translation stage
- [ ] Create glossary applier
- [ ] Update subtitle gen
- [ ] Test end-to-end

### Phase 3: Enhancement
- [ ] Context-aware selection
- [ ] Film-specific rules
- [ ] Learning system
- [ ] Frequency tracking

### Phase 4: Quality
- [ ] Validation tools
- [ ] Automated tests
- [ ] Dashboard
- [ ] Final documentation

---

**Next Action**: `python3 tools/merge_glossaries.py`

**Last Updated**: 2025-11-14  
**Version**: 1.0  
**Status**: Ready to implement
