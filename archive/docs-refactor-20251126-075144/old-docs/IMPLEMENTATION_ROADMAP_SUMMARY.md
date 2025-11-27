# Implementation Roadmap Summary

**Quick Reference for Comprehensive Improvement Plan**

---

## 🎯 What We're Building

Enhance CP-WhisperX-App from **production-ready** to **research-grade** quality by integrating:
- **TMDB** for automatic metadata and glossaries
- **NER** for entity recognition and correction  
- **Enhanced Speaker Diarization** for character mapping
- **Lyrics Database Integration** for official song lyrics

---

## 📊 Expected Improvements

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Character Names | 80% | 95%+ | TMDB + NER |
| Location Names | 70% | 90%+ | Glossary + NER |
| Entity Preservation | 60% | 95%+ | NER in Translation |
| Song Lyrics | 70% | 95%+ | Official Database |
| Manual Work | Hours | Minutes | TMDB Auto-generation |

---

## 🚀 Quick Start (Phase 1)

### Step 1: Get TMDB API Key (5 minutes)
1. Visit: https://www.themoviedb.org/signup
2. Go to Settings → API → Request API Key
3. Choose "Developer" option
4. Add to `config/.env.pipeline`:
   ```bash
   TMDB_API_KEY=your_key_here
   ```

### Step 2: Install Dependencies (10 minutes)
```bash
# Re-run bootstrap with new deps
./bootstrap.sh --update

# Or manually in common venv:
source venv/common/bin/activate
pip install tmdbv3api spacy cachetools
python -m spacy download en_core_web_sm
```

### Step 3: Test TMDB Fetch (5 minutes)
```bash
python scripts/fetch_tmdb_metadata.py \
    --title "Jaane Tu Ya Jaane Na" \
    --year 2008 \
    --output test_glossary.yaml \
    --cache-dir cache/tmdb
```

**Expected Output:**
```yaml
movie: Jaane Tu... Ya Jaane Na
year: 2008
characters:
  - name: Jai Singh Rathore
    actor: Imran Khan
    aliases: [Jai, Rathore]
  - name: Aditi Mahant
    actor: Genelia D'Souza
    aliases: [Aditi]
  - name: Bombs
    actor: Arbaaz Khan
    common_errors: [moms, bonds]
```

### Step 4: Run Test Pipeline
```bash
# Prepare job with TMDB
./prepare-job.sh \
    --media "test-clip.mp4" \
    --workflow subtitle \
    --source-lang hi \
    --target-langs en \
    --tmdb-title "Jaane Tu Ya Jaane Na" \
    --tmdb-year 2008

# Run with NER enabled
./run-pipeline.sh -j <job-id>
```

---

## 📅 Implementation Timeline

### **Phase 1: Foundation** (Weeks 1-2) ← START HERE
**What:** TMDB + NER infrastructure  
**Time:** 2 weeks  
**Effort:** 40-50 hours  

**Week 1:**
- [ ] Add TMDB/NER dependencies to bootstrap
- [ ] Implement `shared/tmdb_client.py`
- [ ] Implement `shared/ner_corrector.py`
- [ ] Implement `shared/glossary_generator.py`
- [ ] Create `scripts/fetch_tmdb_metadata.py`

**Week 2:**
- [ ] Update `prepare-job.sh` for TMDB integration
- [ ] Create `scripts/ner_post_processor.py`
- [ ] Integration testing
- [ ] Basic documentation

**Deliverable:** Auto-generated glossaries + NER correction working

---

### **Phase 2: Pipeline Integration** (Weeks 3-4)
**What:** Integrate into run-pipeline.sh  
**Time:** 2 weeks  
**Effort:** 40-50 hours  

**Tasks:**
- [ ] Add NER stage to pipeline
- [ ] Update `run-pipeline.sh` orchestration
- [ ] Enhance hybrid merger with NER
- [ ] Backward compatibility testing
- [ ] Documentation updates

**Deliverable:** Full pipeline with optional TMDB/NER

---

### **Phase 3: Advanced Features** (Weeks 5-6)
**What:** Speaker diarization + Lyrics DB  
**Time:** 2 weeks  
**Effort:** 40-50 hours  

**Tasks:**
- [ ] PyAnnote speaker diarization
- [ ] TMDB character mapping
- [ ] Lyrics database integration
- [ ] Advanced testing

**Deliverable:** Production-ready advanced features

---

### **Phase 4: Documentation** (Weeks 7-8)
**What:** Complete docs + tutorials  
**Time:** 2 weeks  
**Effort:** 30-40 hours  

**Tasks:**
- [ ] Complete user guides
- [ ] Technical documentation
- [ ] Example workflows
- [ ] Video tutorials

**Deliverable:** Release-ready documentation

---

## 🎓 What You Get at Each Phase

### After Phase 1 (2 weeks):
✅ Automatic character/location glossaries from TMDB  
✅ NER-based entity correction  
✅ Fixes "moms"→"Bombs", "Cup pyrites"→"Cuff Parade"  
✅ 15-20% quality improvement  

**Can use in production!**

### After Phase 2 (4 weeks):
✅ Fully integrated pipeline  
✅ Hybrid translation with NER  
✅ Backward compatible  
✅ Optional feature flags  

**Production-grade quality!**

### After Phase 3 (6 weeks):
✅ Speaker-to-character mapping  
✅ Official song lyrics  
✅ Research-grade features  
✅ 95%+ entity accuracy  

**Best-in-class quality!**

### After Phase 4 (8 weeks):
✅ Complete documentation  
✅ User training materials  
✅ Open-source ready  
✅ Community contribution ready  

**Release-ready product!**

---

## 🔧 Integration Points

### Bootstrap Script
```bash
# scripts/bootstrap.sh - install_common_environment()

# NEW: TMDB and NER libraries
pip install tmdbv3api spacy cachetools
python -m spacy download en_core_web_sm
```

### Prepare Job Script
```bash
# prepare-job.sh

# NEW: TMDB fetch options
--tmdb-title "Movie Name"
--tmdb-year 2008
--no-tmdb  # disable if needed

# Auto-generates: $JOB_DIR/glossary.yaml
```

### Run Pipeline Script
```bash
# run-pipeline.sh

# NEW: NER correction stage (optional)
run_ner_correction "$JOB_DIR"

# Uses: $JOB_DIR/glossary.yaml
# Creates: $JOB_DIR/ner_corrections.json
```

### Configuration
```bash
# config/.env.pipeline

# NEW: TMDB settings
TMDB_ENABLED=true
TMDB_API_KEY=your_key
TMDB_CACHE_DIR=cache/tmdb

# NEW: NER settings
NER_ENABLED=true
NER_MODEL=en_core_web_sm
```

---

## 📁 New Files Created

### Core Modules
```
shared/
├── tmdb_client.py          # TMDB API integration
├── ner_corrector.py        # NER + glossary correction
└── glossary_generator.py   # Auto-generate from TMDB
```

### Scripts
```
scripts/
├── fetch_tmdb_metadata.py  # CLI tool for TMDB fetch
├── ner_post_processor.py   # Pipeline stage
└── speaker_diarization.py  # Advanced feature
```

### Documentation
```
docs/
├── COMPREHENSIVE_IMPROVEMENT_PLAN.md  # Full plan
├── IMPLEMENTATION_ROADMAP_SUMMARY.md  # This file
├── user-guide/
│   ├── glossary-management.md
│   ├── entity-correction.md
│   └── speaker-diarization.md
└── technical/
    ├── tmdb-integration.md
    └── ner-pipeline.md
```

---

## 🧪 Testing Checklist

### Phase 1 Testing
- [ ] TMDB fetch works for "Jaane Tu Ya Jaane Na"
- [ ] Glossary auto-generated with correct characters
- [ ] NER corrects "moms" → "Bombs"
- [ ] NER corrects "Cup pyrites" → "Cuff Parade"
- [ ] Cache system works (no duplicate API calls)

### Phase 2 Testing
- [ ] Pipeline runs with TMDB/NER enabled
- [ ] Pipeline runs without TMDB (fallback works)
- [ ] Backward compatibility (old jobs still work)
- [ ] Hybrid merger with NER improves quality
- [ ] No performance degradation (< 10% overhead)

### Phase 3 Testing
- [ ] Speaker diarization identifies speakers
- [ ] Character mapping works with TMDB
- [ ] Lyrics database fetch works (if available)
- [ ] All features can be toggled independently

---

## 💡 Pro Tips

### For Development
1. **Start small:** Test TMDB fetch first
2. **Use caching:** Avoid hitting API limits
3. **Test offline:** Cache lets you develop without internet
4. **Version control:** Commit after each working module

### For Production
1. **Enable gradually:** Start with TMDB only
2. **Monitor metrics:** Track entity accuracy improvements
3. **User feedback:** Test on diverse content
4. **Fallback plans:** System works without TMDB/NER

### For Debugging
1. **Check logs:** `logs/<job-id>/ner_correction.log`
2. **Review reports:** `$JOB_DIR/ner_corrections.json`
3. **Compare versions:** Before/after NER correction
4. **Test glossaries:** Validate YAML structure

---

## 🚨 Common Issues & Solutions

### Issue: TMDB API Key Not Working
**Solution:**
```bash
# Verify key is set
echo $TMDB_API_KEY

# Test directly
curl "https://api.themoviedb.org/3/movie/550?api_key=$TMDB_API_KEY"
```

### Issue: spaCy Model Not Found
**Solution:**
```bash
# Download manually
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; spacy.load('en_core_web_sm')"
```

### Issue: NER Not Correcting Entities
**Solution:**
- Check glossary has `common_errors` field
- Verify glossary loaded: check logs
- Test NER directly: `python scripts/ner_post_processor.py --help`

---

## 📞 Support & Resources

### Documentation
- **Full Plan:** `docs/COMPREHENSIVE_IMPROVEMENT_PLAN.md`
- **Index:** `docs/INDEX.md`
- **Quick Start:** `docs/QUICKSTART.md`

### External Resources
- **TMDB API:** https://developer.themoviedb.org/docs
- **spaCy NER:** https://spacy.io/usage/linguistic-features
- **PyAnnote:** https://github.com/pyannote/pyannote-audio

### Community
- GitHub Issues (for bugs)
- Discussions (for questions)
- Pull Requests (for contributions)

---

## ✅ Ready to Start?

### Immediate Actions (Today):
1. ⭐ Get TMDB API key (5 minutes)
2. 🔧 Run `./bootstrap.sh --update` (10 minutes)
3. 🧪 Test TMDB fetch on sample movie (5 minutes)
4. 📖 Read full plan: `docs/COMPREHENSIVE_IMPROVEMENT_PLAN.md`

### This Week:
5. 💻 Implement Phase 1 core modules
6. 🧪 Test on your "Jaane Tu Ya Jaane Na" clip
7. 📝 Document learnings

### Next Week:
8. 🔗 Pipeline integration
9. 🧪 End-to-end testing
10. 🚀 Production deployment

---

**Let's make your subtitles perfect! 🎬✨**

---

*Quick Reference Version 1.0*  
*See `docs/COMPREHENSIVE_IMPROVEMENT_PLAN.md` for full details*  
*Last Updated: November 24, 2025*
