# BRD: Workflow-Specific Output Requirements

**ID:** BRD-2025-12-05-02  
**Created:** 2025-12-05  
**Status:** Approved  
**Priority:** High  
**Target Release:** v3.0

---

## Business Objective

**Problem Statement:**
All three workflows (transcribe, translate, subtitle) currently generate subtitle files, even when users only requested text transcripts. This violates user expectations and wastes processing time.

**Proposed Solution:**
Implement workflow-aware stage selection that produces ONLY the requested output type:
- **Transcribe:** Text transcript only (NO subtitles)
- **Translate:** Translated text only (NO subtitles)
- **Subtitle:** Video with embedded subtitles (ONLY workflow that creates subtitles)

---

## Stakeholder Requirements

### Primary Stakeholders
- **Role:** End Users
  - **Need:** Receive only the output they requested
  - **Expected Outcome:** 
    - Transcribe → transcript.txt
    - Translate → transcript_en.txt
    - Subtitle → media_with_subs.mkv

---

## Success Criteria

### Quantifiable Metrics
- [ ] Transcribe workflow: NO subtitle files generated
- [ ] Translate workflow: NO subtitle files generated
- [ ] Subtitle workflow: Subtitles properly embedded
- [ ] Processing time: Reduced by 15-30% for transcribe/translate (skip subtitle stages)

### Qualitative Measures
- [ ] User expectations met (text when requested, subtitles only when requested)
- [ ] Clear separation of concerns

---

## Scope

### In Scope
- Workflow-aware stage selection in run-pipeline
- Skip subtitle_generation and mux for transcribe/translate workflows
- Export transcript text files instead
- Update documentation

### Out of Scope
- Changing subtitle generation logic itself
- Modifying individual stages
- Adding new output formats

---

## Related Documents

- **TRD:** [TRD-2025-12-05-02-workflow-outputs.md](../../trd/TRD-2025-12-05-02-workflow-outputs.md)
- **Implementation Tracker:** IMPLEMENTATION_TRACKER.md § AD-010
- **Architectural Decision:** ARCHITECTURE.md § AD-010

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | Ravi Patel | 2025-12-05 | ✅ Approved |

---

**Status Log:**

| Date | Status Change | Notes |
|------|---------------|-------|
| 2025-12-05 | Draft → Approved | AD-010 established |
| 2025-12-08 | Backfilled to BRD | Pending implementation |
