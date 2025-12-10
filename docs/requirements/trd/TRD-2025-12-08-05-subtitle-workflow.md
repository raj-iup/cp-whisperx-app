# TRD: Multi-Phase Subtitle Workflow with Learning

**ID:** TRD-2025-12-08-05  
**Created:** 2025-12-08  
**Status:** Approved  
**Related BRD:** [BRD-2025-12-08-05](../brd/BRD-2025-12-08-05-subtitle-workflow.md)

---

## Technical Overview

Implement intelligent caching for subtitle workflow to enable fast iterative refinement.

---

## Architecture Changes

### Cache Structure
```
cache/
└── media/
    └── {media_id}/
        ├── baseline/          # Phase 1 artifacts
        │   ├── audio.wav
        │   ├── segments.json
        │   ├── aligned.json
        │   ├── vad.json
        │   └── metadata.json
        ├── glossary/          # Phase 2 artifacts
        │   └── {glossary_hash}/
        │       ├── applied.json
        │       └── quality_metrics.json
        └── translations/      # Phase 3 artifacts
            └── {target_lang}/
                └── translated.json
```

---

## Implementation Requirements

### New Files

**`shared/media_identity.py`:**
```python
def compute_media_id(media_path: Path) -> str:
    """
    Compute stable identifier from audio content.
    
    Uses SHA256 of audio samples (not file metadata).
    Same audio = same ID, even if filename changes.
    """
    # Extract audio
    # Sample at multiple points
    # Compute SHA256 hash
    return media_id
```

**`shared/cache_manager.py`:**
```python
class MediaCacheManager:
    def has_baseline(self, media_id: str) -> bool:
        """Check if baseline exists for media"""
        
    def get_baseline(self, media_id: str) -> BaselineArtifacts:
        """Load cached baseline"""
        
    def store_baseline(self, media_id: str, artifacts: BaselineArtifacts):
        """Save baseline artifacts"""
        
    def has_glossary_results(self, media_id: str, glossary_hash: str) -> bool:
        """Check if glossary-applied results exist"""
        
    def get_glossary_results(self, media_id: str, glossary_hash: str):
        """Load cached glossary results"""
        
    def store_glossary_results(self, media_id: str, glossary_hash: str, results):
        """Save glossary-applied results"""
```

### Modified Files

**`run-pipeline.py`:**
```python
def _execute_subtitle_workflow(self):
    # Compute media ID
    media_id = compute_media_id(self.media_file)
    
    # Check for baseline
    cache_mgr = MediaCacheManager()
    if cache_mgr.has_baseline(media_id):
        logger.info("✅ Found cached baseline, loading...")
        baseline = cache_mgr.get_baseline(media_id)
        # Skip stages 01-07
    else:
        logger.info("🆕 No cache found, generating baseline...")
        baseline = self._run_baseline_generation()
        cache_mgr.store_baseline(media_id, baseline)
    
    # Check for glossary results
    glossary_hash = compute_glossary_hash(self.glossary_file)
    if cache_mgr.has_glossary_results(media_id, glossary_hash):
        logger.info("✅ Found cached glossary results, loading...")
        # Skip glossary application
    else:
        logger.info("🆕 Applying glossary...")
        results = apply_glossary(baseline, self.glossary_file)
        cache_mgr.store_glossary_results(media_id, glossary_hash, results)
    
    # Continue with translation and subtitle generation
```

---

## Design Decisions

### Decision 1: Media Identity Method
**Problem:** How to identify "same media" across runs

**Options:**
1. Filename - ❌ Rejected: Changes break cache
2. File hash - ❌ Rejected: Re-encoding breaks cache
3. Audio content hash - ✅ Selected: Stable across file changes

**Rationale:** Audio content hash is stable even if user renames file or re-encodes video

### Decision 2: Cache Invalidation
**Problem:** When to invalidate cache

**Invalidation Triggers:**
- User flag: `--no-cache`
- Model version change
- Major quality degradation

**Automatic Retention:**
- Keep cache for 90 days
- LRU eviction if disk space limited

---

## Testing Requirements

### Integration Tests
```python
# tests/integration/test_subtitle_caching.py

def test_baseline_caching():
    """Verify baseline is cached and reused"""
    # First run
    result1 = run_subtitle_workflow("movie.mp4")
    time1 = result1.duration
    
    # Second run (should use cache)
    result2 = run_subtitle_workflow("movie.mp4")
    time2 = result2.duration
    
    assert time2 < time1 * 0.3, "Second run should be 70% faster"
    assert result1.baseline == result2.baseline

def test_glossary_refinement():
    """Verify glossary updates use cached baseline"""
    # Initial run
    result1 = run_subtitle_workflow("movie.mp4", glossary1)
    
    # Update glossary
    glossary2 = update_glossary(glossary1, {"Simran": "सिमरन"})
    
    # Second run (should reuse baseline)
    result2 = run_subtitle_workflow("movie.mp4", glossary2)
    
    assert result2.baseline_cache_hit == True
    assert "सिमरन" in result2.subtitles
```

---

## Documentation Updates

- [ ] **User Guide:** Multi-phase workflow documentation
- [ ] **ARCHITECTURE.md:** AD-014 section
- [ ] **Quickstart:** Cache usage examples
- [ ] **TROUBLESHOOTING.md:** Cache debugging

---

## Performance Considerations

**Expected Performance:**
- First run: 15-20 minutes (baseline generation)
- Glossary update: 3-6 minutes (reuse baseline, 70-80% faster)
- Translation refresh: 2-4 minutes per language (reuse baseline + glossary)
- Cache storage: ~500MB per movie

**Optimization:**
- Lazy loading of cache artifacts
- Incremental cache updates
- Background cache warming

---

## Related Documents

- **BRD:** [BRD-2025-12-08-05-subtitle-workflow.md](../brd/BRD-2025-12-08-05-subtitle-workflow.md)
- **AD-014:** ARCHITECTURE.md § AD-014

---

**Version:** 1.0 | **Status:** Approved (Pending Implementation)  
**Effort:** 1-2 weeks
