# BRD: Online Media Source Integration

**ID:** BRD-2025-12-10-02  
**Created:** 2025-12-10  
**Status:** Draft  
**Priority:** High  
**Target Release:** v3.1

---

## Business Objective

### Why This is Needed

**Problem Statement:**
Users currently must manually download videos from online sources (YouTube, Vimeo, etc.) before processing them with CP-WhisperX-App. This creates friction in the workflow and limits accessibility, especially for users who want to process online content directly.

**Background:**
- Online video platforms (YouTube, Vimeo, Dailymotion) host billions of videos
- Users have subscriptions to various platforms (YouTube Premium, Vimeo Plus)
- Manual download-then-process workflow is inefficient and error-prone
- Current tools require external utilities (browser extensions, separate download tools)
- Competitors lack unified online media integration

**Market Opportunity:**
- **Content Creators:** Need to transcribe/translate online video content at scale
- **Researchers:** Analyze lecture content, interviews, podcasts from various platforms
- **Bollywood Fans:** Add subtitles to music videos, movie clips, trailers
- **Language Learners:** Translate educational content for study
- **Media Companies:** Process online archives for accessibility

**Proposed Solution:**
Enable users to provide online media URLs via the universal `--media` parameter. The system automatically detects whether the media source is:
- **Online URL** (starts with http://, https://) → Download then process
- **Local path** (file/directory) → Process directly

**Phase 1 Focus:** YouTube integration (Premium accounts only)
**Future Phases:** Expand to other online media providers (Vimeo, Dailymotion, SoundCloud, etc.)

---

## Stakeholder Requirements

### Primary Stakeholders

**1. Content Creators**
- **Need:** Process online videos without manual download
- **Expected Outcome:** Single command to transcribe/translate online content using universal `--media` parameter
- **Success Metric:** 90% time reduction in workflow setup

**2. Researchers & Educators**
- **Need:** Transcribe online lectures and interviews from various platforms
- **Expected Outcome:** Accurate transcripts from online media URLs
- **Success Metric:** 100% success rate for accessible videos (Premium accounts)

**3. Bollywood/Media Enthusiasts**
- **Need:** Add multilingual subtitles to online video clips
- **Expected Outcome:** Professional subtitle tracks for online videos
- **Success Metric:** 88%+ subtitle quality maintained

**4. Multilingual Users**
- **Need:** Translate online video content to native language
- **Expected Outcome:** Accurate translations preserving cultural context
- **Success Metric:** BLEU score ≥90% maintained

### Secondary Stakeholders

**5. Developers**
- **Impact:** Clean integration with existing pipeline
- **Need:** Minimal code changes, reusable across workflows
- **Success Metric:** <500 LOC, passes all compliance checks

**6. System Administrators**
- **Impact:** Additional dependency (yt-dlp)
- **Need:** Stable, well-maintained library
- **Success Metric:** Zero system instability

---

## Success Criteria

### Quantifiable Metrics

- [x] **Adoption:** 50%+ of new jobs use online URLs within 1 month
- [x] **Success Rate:** 95%+ download success for accessible videos (with Premium accounts)
- [x] **Performance:** <5 minutes download time for typical video
- [x] **Quality:** No degradation in ASR/translation/subtitle quality
- [x] **Reliability:** <1% failure rate (excluding unavailable videos)
- [x] **Auto-detection:** 100% accurate URL vs. local path detection

### Qualitative Measures

- [x] **User Satisfaction:** Positive feedback from early adopters
- [x] **Workflow Simplification:** Eliminates manual download step
- [x] **Competitive Advantage:** Feature not offered by competitors
- [x] **Documentation Quality:** Clear examples for all workflows
- [x] **Error Handling:** Graceful failures with actionable messages

---

## Scope

### In Scope

**Phase 1 (MVP - YouTube Only):**
- ✅ Universal `--media` parameter (accepts URLs or local paths)
- ✅ Auto-detection: URL vs. local path based on parameter value
- ✅ YouTube video download (Premium accounts REQUIRED)
- ✅ Support for all three workflows (transcribe, translate, subtitle)
- ✅ Automatic format selection (best quality MP4)
- ✅ Basic error handling and validation
- ✅ YouTube Premium authentication (mandatory for YouTube)
- ✅ Cached downloads (prevent re-downloading)

**Phase 2 (Enhancement & Expansion):**
- ✅ Quality selection (1080p, 720p, 480p, audio-only)
- ✅ Playlist support (batch processing)
- ✅ Live stream recording
- ✅ Resume interrupted downloads
- ✅ **Additional online media sources:**
  - Vimeo (with Vimeo Plus/Premium)
  - Dailymotion
  - SoundCloud
  - Generic video URLs (direct links)

### Out of Scope

- ❌ Video upload to online platforms
- ❌ Platform API integration (comments, likes, analytics)
- ❌ Live streaming analysis (real-time)
- ❌ Copyright/licensing management
- ❌ Platform Studio/Creator tools integration
- ❌ Video editing features
- ❌ Social/Community features
- ❌ Free YouTube account support (Premium only)

### Future Considerations

**Post-v3.1 Enhancements:**
- Playlist batch processing (v3.2)
- Channel-wide processing (v3.2)
- Live stream archiving (v3.3)
- Platform metadata extraction (v3.3)
- **Multi-platform support (v3.2):**
  - Vimeo integration
  - Dailymotion integration
  - SoundCloud integration
  - Generic URL support
- Auto-upload processed videos (v4.0)

---

## Dependencies

### Internal Dependencies

**Required CP-WhisperX Components:**
- ✅ `prepare-job.sh` - Modify `--media` parameter logic to detect URLs
- ✅ `shared/config_loader.py` - Configuration management
- ✅ `shared/logger.py` - Logging infrastructure
- ✅ `shared/media_detector.py` - NEW: Auto-detect URL vs. local path
- ✅ Existing pipeline stages (01-12) - Unchanged

**Configuration Dependencies:**
- ✅ `config/.env.pipeline` - System-wide settings
- ✅ `config/user.profile` - User-specific persistent settings (NEW)
- ✅ Job directory structure - File placement

### External Dependencies

**Primary Dependency:**
- **yt-dlp** (v2024.8.6+)
  - Modern, actively maintained online media downloader
  - Replaces deprecated youtube-dl
  - **Supports 1000+ sites** (YouTube, Vimeo, Dailymotion, etc.)
  - Premium account support for major platforms
  - Format selection and quality control
  - License: Unlicense (public domain)
  - Installation: `pip install yt-dlp`

**System Requirements:**
- ✅ Python 3.11+ (already required)
- ✅ Network connectivity (internet access)
- ✅ Storage space (video downloads)

### Prerequisites

**Before Implementation:**
- ✅ BRD-PRD-TRD approval
- ✅ Architecture review (AD-015: User profile architecture)
- ✅ Dependency security audit (yt-dlp)
- ✅ Storage planning (online media cache directory)
- ✅ User profile format specification

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **Platform rate limiting** | Medium | Low | Use Premium authentication, implement exponential backoff, cache downloads |
| **Video unavailable/private** | Low | Medium | Pre-validation before download, clear error messages, Premium required |
| **Large file timeout** | Medium | Medium | Configurable timeout (default 30 min), progress reporting |
| **Format compatibility** | High | Low | Use yt-dlp's smart format selection (MP4 preferred) |
| **Copyright/DMCA issues** | Medium | Low | User responsibility disclaimer, Premium accounts, no redistribution |
| **yt-dlp maintenance** | High | Low | Pin version, monitor repo, active community support |
| **Premium auth security** | High | Low | User profile storage, never log credentials, required for YouTube |
| **Storage exhaustion** | Medium | Low | Configurable cache size, automatic cleanup, user warnings |
| **URL detection errors** | Low | Low | Robust regex patterns, clear validation errors, user feedback |

---

## Timeline & Resources

### Estimated Effort

**Total: 8-10 hours**

**Phase 1 (MVP - YouTube Only):**
- BRD-PRD-TRD Documentation: 2 hours ✅ (This document)
- Implementation: 5 hours
  - shared/media_detector.py: 0.5 hours (URL detection logic)
  - scripts/online_media_downloader.py: 1.5 hours
  - shared/user_profile.py: 0.5 hours (NEW - user profile manager)
  - prepare-job.sh integration: 1.5 hours (modify --media logic + profile extraction)
  - Configuration: 0.5 hours (user.profile template)
  - Requirements: 0.5 hours
- Testing: 1.5 hours
  - Unit tests: 0.5 hours
  - Integration tests: 0.5 hours
  - Manual testing: 0.5 hours
- Documentation: 1.5 hours
  - README updates: 0.5 hours
  - Workflow examples: 0.5 hours
  - Troubleshooting guide: 0.5 hours

**Phase 2 (Enhancement & Multi-platform):**
- Quality selection: 1 hour
- Playlist support: 2 hours
- Live stream: 3 hours
- Resume downloads: 2 hours
- Additional platforms (Vimeo, Dailymotion, etc.): 3 hours

### Required Resources

**Development:**
- 1 developer (full-stack)
- Access to YouTube account (public + premium)
- Test videos (public, unlisted, private)

**Testing:**
- Public/Premium YouTube videos (various lengths)
- YouTube Premium account (required for authentication)
- Local files (to test auto-detection)
- URLs vs. paths (edge cases)
- Network conditions (fast, slow, interrupted)

**Infrastructure:**
- No additional infrastructure needed
- Uses existing pipeline architecture

---

## Business Value

### Revenue Impact

**Direct Revenue:**
- ✅ Increased user adoption (ease of use)
- ✅ Premium feature differentiation
- ✅ Competitive advantage (unique feature)

**Indirect Revenue:**
- ✅ Expanded addressable market (YouTube content creators)
- ✅ Reduced churn (improved workflow)
- ✅ Word-of-mouth marketing (unique capability)

### Cost Savings

**User Time:**
- Before: 5-10 minutes manual download per online video
- After: 0 minutes (automated via `--media` URL)
- **Savings: 100% time reduction for download step**
- **Bonus: Universal interface** (same `--media` parameter for all sources)

**System Resources:**
- Minimal impact (downloads happen locally)
- Cached downloads prevent duplication
- **No additional infrastructure costs**

### Strategic Value

**Market Position:**
- ✅ First-mover advantage (unified online media integration)
- ✅ Universal `--media` interface (local + online)
- ✅ Differentiation from competitors
- ✅ Enables new use cases (multi-platform content workflows)
- ✅ Scalable architecture (easy to add new platforms)

**User Experience:**
- ✅ Simplified workflow (one command instead of two steps)
- ✅ Professional appearance (integrated solution)
- ✅ Reduced friction (no external tools needed)

---

## Compliance & Legal

### Copyright Considerations

**User Responsibility:**
- Users must have rights to process content
- Downloading for personal use (fair use doctrine)
- Premium accounts required (respects platform Terms of Service)
- No redistribution features provided
- Clear disclaimer in documentation

**DMCA Compliance:**
- Tool is content-neutral (doesn't host content)
- Respects platform Terms of Service (Premium tier for YouTube)
- No circumvention of DRM/protection measures
- Premium requirement ensures ToS compliance

### Privacy Considerations

**Authentication:**
- Credentials stored in user profile (never transmitted to us)
- **Required for YouTube** (Premium accounts only)
- Optional for other platforms (Phase 2)
- **Stored in:** `config/user.profile` (persistent, user-specific)
- **Architecture:** User profile → Job config (extracted per job)
- App-specific passwords recommended for 2FA accounts
- User profile remains permanent until user deletes it

**Data Handling:**
- No telemetry on online media usage
- No video content stored permanently (user's local cache)
- No sharing of user activity
- **User profiles stored locally only** (never synchronized or transmitted)
- User controls profile data (can delete anytime)

---

## Approval & Sign-off

**Business Approval:**
- [ ] Product Owner: _____________________ Date: _______
- [ ] Business Stakeholder: ______________ Date: _______

**Technical Approval:**
- [ ] Lead Developer: ____________________ Date: _______
- [ ] Architect: _________________________ Date: _______

**Go/No-Go Decision:**
- [ ] **GO** - Proceed to PRD and implementation
- [ ] **NO-GO** - Defer or cancel with reason: ___________

---

## Related Documents

**Downstream Documents:**
- [PRD-2025-12-10-02-online-media-integration.md](../prd/PRD-2025-12-10-02-online-media-integration.md) (Next)
- [TRD-2025-12-10-02-online-media-integration.md](../trd/TRD-2025-12-10-02-online-media-integration.md) (Next)

**Reference Documents:**
- [DEVELOPER_STANDARDS.md](../../DEVELOPER_STANDARDS.md) - § 21 BRD-PRD-TRD Framework
- [BRD-PRD-TRD-IMPLEMENTATION-FRAMEWORK.md](../../../BRD-PRD-TRD-IMPLEMENTATION-FRAMEWORK.md)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) - No AD changes required

**Related BRDs:**
- None (standalone feature)

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-10  
**Next Review:** Upon PRD completion
