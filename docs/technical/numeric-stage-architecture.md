# Numeric-Only Stage Architecture Decision

**Date:** 2025-12-04  
**Decision:** Use NUMBERS ONLY for stage naming (no letters like 11a, 11b)  
**Rationale:** Cleaner, simpler, more maintainable, easier tooling support  
**Status:** ✅ Approved Architecture

---

## 🎯 Architecture Decision

### Approved Stage Numbering (Numeric Only):

```
Stage 01: Demux
Stage 02: TMDB Enrichment
Stage 03: Glossary Load
Stage 04: Source Separation
Stage 05: PyAnnote VAD
Stage 06: WhisperX ASR
Stage 07: Alignment
Stage 08: Lyrics Detection
Stage 09: Hallucination Removal
Stage 10: Translation Prep
Stage 11: IndicTrans2 Translation
Stage 12: NLLB Translation
Stage 13: Translation Merge
Stage 14: Subtitle Generation
Stage 15: Mux
```

**Total: 15 stages in complete pipeline**

---

## 📁 File Naming Standard

**Format:** `{NN}_{stage_name}.py`

Where `NN` = 01-99 (two digits, zero-padded, numbers only)

**Examples:**
- ✅ `scripts/10_translation_prep.py`
- ✅ `scripts/11_indictrans2_translation.py`
- ✅ `scripts/14_subtitle_generation.py`
- ❌ `scripts/11a_indictrans2_translation.py` (NO LETTERS)
- ❌ `scripts/11_a_translation.py` (NO LETTERS)

---

## 🔄 Directory Naming Standard

**Format:** `{NN}_{stage_name}/`

**Examples:**
- ✅ `out/{job}/10_translation_prep/`
- ✅ `out/{job}/11_indictrans2_translation/`
- ❌ `out/{job}/11a_indictrans2/` (NO LETTERS)

---

## ✅ Benefits

1. **Simplicity:** No sub-numbering confusion
2. **Clarity:** Clear sequential order
3. **Tooling:** Better file manager/script support
4. **Standards:** Follows common pipeline conventions
5. **Sorting:** Natural alphabetical = execution order
6. **Scalability:** Room for 99 stages
7. **Maintainability:** Easier to understand and modify

---

## 📋 Migration Plan

### Current → New Mapping:

| Current | New | Action |
|---------|-----|--------|
| `10_translation.py` | Split into 10,11,12,13 | Create 4 new stages |
| `11_subtitle_generation.py` | `14_subtitle_generation.py` | Rename |
| `12_mux.py` | `15_mux.py` | Rename |

### New Files to Create:

1. `scripts/10_translation_prep.py` - Routing & planning
2. `scripts/11_indictrans2_translation.py` - Indic translation
3. `scripts/12_nllb_translation.py` - Non-Indic translation
4. `scripts/13_translation_merge.py` - Merge results

---

## 🔗 Stage Dependencies

```
10 → 11 (IndicTrans2 - if needed)
10 → 12 (NLLB - if needed)
11 → 13 (Merge)
12 → 13 (Merge)
13 → 14 (Subtitle Gen)
14 → 15 (Mux)
```

**Note:** Stages 11 and 12 can run in parallel (future optimization)

---

## 📊 Workflows

### Transcribe Workflow:
```
01 → 04 → 05 → 06 → 07
(5 stages)
```

### Translate Workflow:
```
01 → 04 → 05 → 06 → 07 → 10 → 11/12 → 13
(8-9 stages)
```

### Subtitle Workflow:
```
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11/12 → 13 → 14 → 15
(15 stages)
```

---

**Status:** ✅ Approved  
**Effective:** 2025-12-04  
**Supersedes:** Sub-letter numbering (11a, 11b, 11c, etc.)
