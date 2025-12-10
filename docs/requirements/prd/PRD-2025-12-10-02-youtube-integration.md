# Product Requirement Document (PRD): YouTube Video Integration

**PRD ID:** PRD-2025-12-10-02-youtube-integration  
**Related BRD:** [BRD-2025-12-10-02-youtube-integration](../brd/BRD-2025-12-10-02-youtube-integration.md)  
**Status:** Draft  
**Owner:** Product Manager  
**Created:** 2025-12-10  
**Last Updated:** 2025-12-10

---

## I. Introduction

### Purpose

This PRD defines the product requirements for integrating YouTube video download capability into CP-WhisperX-App, enabling users to process YouTube content directly without manual download steps.

**Business Context** (from BRD-2025-12-10-02):
- Simplifies workflow by eliminating manual download step
- Expands addressable market to YouTube content creators
- Provides competitive differentiation
- Supports all three workflows (transcribe, translate, subtitle)

### Definitions/Glossary

| Term | Definition |
|------|------------|
| **yt-dlp** | Modern, actively maintained YouTube video downloader library |
| **YouTube URL** | Direct link to YouTube video (watch, youtu.be, shorts formats) |
| **Premium Account** | YouTube Premium subscription (ad-free, higher quality) |
| **Format Selection** | Choosing video quality (best, 1080p, 720p, 480p, audio-only) |
| **Sanitized Filename** | Video title cleaned for filesystem compatibility |
| **Cache Directory** | Local storage for downloaded videos (`in/youtube/`) |

---

## II. User Personas & Flows

### User Personas

#### Persona 1: Content Creator Casey
**Demographics:**
- Age: 28, Location: Mumbai
- Role: YouTube content creator (Bollywood analysis)
- Tech Savvy: High

**Goals:**
- Transcribe Hindi YouTube videos to text
- Translate Hindi content to English for subtitles
- Process multiple videos efficiently

**Pain Points:**
- Manual download takes 5-10 minutes per video
- Forgetting to download in correct format
- Managing download tools separately

**User Story:**
> "As a content creator, I want to provide a YouTube URL and get transcripts/subtitles automatically, so that I can focus on content analysis instead of technical setup."

---

#### Persona 2: Researcher Rita
**Demographics:**
- Age: 35, Location: Bangalore
- Role: Academic researcher (linguistics)
- Tech Savvy: Medium

**Goals:**
- Transcribe English YouTube lectures
- Analyze speech patterns in educational content
- Build corpus from online lectures

**Pain Points:**
- Doesn't know which downloader to use
- Worried about quality loss during download
- Batch processing is cumbersome

**User Story:**
> "As a researcher, I want to trust that YouTube videos are downloaded in highest quality, so that my transcription accuracy is not compromised."

---

#### Persona 3: Bollywood Fan Bhav
**Demographics:**
- Age: 22, Location: Ahmedabad
- Role: Movie enthusiast, language learner
- Tech Savvy: Low-Medium

**Goals:**
- Add English/Gujarati subtitles to Hindi songs
- Share subtitled clips with friends
- Learn Hindi through Bollywood content

**Pain Points:**
- Complex download tools are intimidating
- Wants "just paste URL and go" experience
- Doesn't understand technical jargon

**User Story:**
> "As a movie fan, I want to paste a YouTube link and get subtitles, so that I don't have to learn complicated download tools."

---

### User Journey/Flows

#### Flow 1: YouTube Transcribe Workflow

```
User has YouTube URL
       ↓
Opens terminal, runs prepare-job.sh
       ↓
Provides --youtube-url parameter
       ↓
System validates URL format
       ↓
System downloads video (shows progress)
       ↓
System runs transcription pipeline
       ↓
User receives transcript file
```

**Expected Duration:** 2-5 minutes (download) + pipeline time

---

#### Flow 2: YouTube Translate Workflow

```
User has Hindi YouTube video URL
       ↓
Runs prepare-job.sh with --youtube-url and --workflow translate
       ↓
System downloads video
       ↓
System detects Hindi audio
       ↓
System translates to English
       ↓
User receives English transcript
```

**Expected Duration:** 2-5 minutes (download) + pipeline time

---

#### Flow 3: YouTube Subtitle Workflow

```
User has Bollywood song/clip URL
       ↓
Runs prepare-job.sh with --youtube-url and --workflow subtitle
       ↓
System downloads video
       ↓
System generates multilingual subtitles
       ↓
System embeds subtitles in video
       ↓
User receives video with soft-embedded subtitles
```

**Expected Duration:** 2-5 minutes (download) + pipeline time

---

## III. Functional Requirements

### Feature List

#### Must-Have (MVP - Phase 1)

**F-001: YouTube URL Validation**
- Priority: Must-have
- Description: Validate YouTube URL before attempting download
- Acceptance Criteria:
  - ✅ Accepts youtube.com/watch?v=ID format
  - ✅ Accepts youtu.be/ID format
  - ✅ Accepts youtube.com/shorts/ID format
  - ✅ Rejects invalid URLs with clear error message
  - ✅ Validates URL accessibility before download

**F-002: Video Download**
- Priority: Must-have
- Description: Download video/audio from YouTube URL
- Acceptance Criteria:
  - ✅ Downloads highest quality MP4 by default
  - ✅ Saves to `in/youtube/` directory
  - ✅ Uses sanitized video title as filename
  - ✅ Shows download progress
  - ✅ Completes within 5 minutes for typical video (<100MB)
  - ✅ Handles network interruptions gracefully

**F-003: Workflow Integration**
- Priority: Must-have
- Description: Integrate with existing transcribe/translate/subtitle workflows
- Acceptance Criteria:
  - ✅ Works with `--workflow transcribe`
  - ✅ Works with `--workflow translate`
  - ✅ Works with `--workflow subtitle`
  - ✅ Downloaded file passed to pipeline automatically
  - ✅ No changes to existing stage code required

**F-004: Error Handling**
- Priority: Must-have
- Description: Handle download failures gracefully
- Acceptance Criteria:
  - ✅ Clear error message for unavailable videos
  - ✅ Clear error message for private/deleted videos
  - ✅ Clear error message for network failures
  - ✅ Clear error message for invalid URL format
  - ✅ Cleanup partial downloads on failure

**F-005: Premium Account Support**
- Priority: Must-have
- Description: Authenticate with YouTube Premium accounts
- Acceptance Criteria:
  - ✅ Optional username/password in config
  - ✅ Works without authentication for public videos
  - ✅ Enables private video access with authentication
  - ✅ Never logs credentials
  - ✅ Secure credential storage (config file only)

#### Should-Have (Phase 1 Enhancement)

**F-006: Quality Selection**
- Priority: Should-have
- Description: Allow users to specify video quality
- Acceptance Criteria:
  - ✅ Support for "best" (default)
  - ✅ Support for 1080p, 720p, 480p
  - ✅ Support for audio-only
  - ✅ Fallback to next best if requested not available
  - ✅ Configuration via .env.pipeline

**F-007: Download Caching**
- Priority: Should-have
- Description: Prevent re-downloading same video
- Acceptance Criteria:
  - ✅ Check cache before download
  - ✅ Use video ID as cache key
  - ✅ Reuse cached file if exists
  - ✅ Configurable cache expiration
  - ✅ Manual cache clear option

#### Could-Have (Phase 2 - Future)

**F-008: Playlist Support**
- Priority: Could-have (Phase 2)
- Description: Download and process entire playlists
- Deferred to: v3.2

**F-009: Live Stream Recording**
- Priority: Could-have (Phase 2)
- Description: Record and process live streams
- Deferred to: v3.3

**F-010: Resume Downloads**
- Priority: Could-have (Phase 2)
- Description: Resume interrupted downloads
- Deferred to: v3.2

---

## IV. User Stories & Acceptance Criteria

### US-001: Basic YouTube Download

**As a** content creator  
**I want to** provide a YouTube URL instead of a local file  
**So that** I can skip the manual download step

**Acceptance Criteria:**
- [ ] Given a valid YouTube URL
  - When I run `prepare-job.sh --youtube-url "URL"`
  - Then the video is downloaded to `in/youtube/`
  - And the filename is the sanitized video title
  - And the file format is MP4

- [ ] Given an invalid YouTube URL
  - When I run `prepare-job.sh --youtube-url "INVALID"`
  - Then I see error message: "Invalid YouTube URL"
  - And no download is attempted
  - And the script exits with code 1

**Test Cases:**
```bash
# TC-001: Valid public video
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --workflow transcribe
# Expected: Downloads successfully, proceeds to transcription

# TC-002: Invalid URL
./prepare-job.sh \
  --youtube-url "https://example.com/video"
# Expected: Error message, exit code 1

# TC-003: Unavailable video
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=INVALID123"
# Expected: Error message "Video not available", exit code 1
```

---

### US-002: YouTube Transcribe Workflow

**As a** researcher  
**I want to** transcribe YouTube lectures directly  
**So that** I can analyze content without manual download

**Acceptance Criteria:**
- [ ] Given a YouTube URL with English audio
  - When I run transcribe workflow with YouTube URL
  - Then video is downloaded
  - And audio is extracted (Stage 01)
  - And transcription is performed (Stages 04-07)
  - And transcript file is created in output directory
  - And transcript accuracy is ≥95% WER

**Test Cases:**
```bash
# TC-004: English YouTube video
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=LECTURE_ID" \
  --workflow transcribe \
  --source-language en

# Expected Output:
# - Downloaded: in/youtube/lecture_title.mp4
# - Transcript: out/.../07_alignment/transcript.txt
# - WER: ≤5%
```

---

### US-003: YouTube Translate Workflow

**As a** multilingual content creator  
**I want to** translate Hindi YouTube videos to English  
**So that** I can reach international audiences

**Acceptance Criteria:**
- [ ] Given a YouTube URL with Hindi audio
  - When I run translate workflow with YouTube URL
  - Then video is downloaded
  - And Hindi is transcribed (Stages 04-07)
  - And content is translated to English (Stage 10)
  - And English transcript file is created
  - And translation BLEU score is ≥90%

**Test Cases:**
```bash
# TC-005: Hindi YouTube video
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=HINDI_ID" \
  --workflow translate \
  --source-language hi \
  --target-language en

# Expected Output:
# - Downloaded: in/youtube/hindi_video_title.mp4
# - Transcript: out/.../10_translation/transcript_en.txt
# - BLEU: ≥90%
```

---

### US-004: YouTube Subtitle Workflow

**As a** Bollywood fan  
**I want to** add English subtitles to Hindi YouTube clips  
**So that** I can share with non-Hindi speakers

**Acceptance Criteria:**
- [ ] Given a YouTube URL with Hindi audio
  - When I run subtitle workflow with YouTube URL
  - Then video is downloaded
  - And full subtitle pipeline runs (Stages 01-12)
  - And video with embedded subtitles is created
  - And subtitle quality is ≥88%
  - And original video quality is preserved

**Test Cases:**
```bash
# TC-006: Hindi music video
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=SONG_ID" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu

# Expected Output:
# - Downloaded: in/youtube/song_title.mp4
# - Output: out/.../12_mux/song_title_subtitled.mp4
# - Subtitles: hi (original), en, gu
# - Quality: ≥88%
```

---

### US-005: Premium Account Authentication

**As a** premium YouTube subscriber  
**I want to** use my account credentials  
**So that** I can access private/unlisted videos

**Acceptance Criteria:**
- [ ] Given YouTube username and password in config
  - When I download a private video I have access to
  - Then authentication is performed
  - And video is downloaded successfully
  - And no credentials are logged

- [ ] Given no credentials in config
  - When I download a public video
  - Then download succeeds without authentication

**Test Cases:**
```bash
# TC-007: Premium account (manual test)
# 1. Add credentials to config/.env.pipeline
# 2. Run with private video URL
# 3. Verify download succeeds
# 4. Check logs for no credential leakage

# TC-008: Public video without credentials
# 1. Remove credentials from config
# 2. Run with public video URL
# 3. Verify download succeeds
```

---

### US-006: Quality Selection

**As a** user with limited storage  
**I want to** select video quality  
**So that** I can balance quality and file size

**Acceptance Criteria:**
- [ ] Given quality setting in config
  - When I download video
  - Then video is downloaded at specified quality
  - And file size is appropriate for quality

- [ ] Given quality not available
  - When I download video
  - Then next best quality is downloaded
  - And user is informed of fallback

**Test Cases:**
```bash
# TC-009: 720p quality
# config/.env.pipeline: YOUTUBE_QUALITY=720p
./prepare-job.sh --youtube-url "URL" --workflow transcribe
# Expected: Downloads 720p version

# TC-010: Audio only
# config/.env.pipeline: YOUTUBE_QUALITY=audio_only
./prepare-job.sh --youtube-url "URL" --workflow transcribe
# Expected: Downloads audio only (smaller file)
```

---

## V. Command-Line Interface

### New Parameter

**`--youtube-url <URL>`**
- **Type:** String (URL)
- **Required:** No (alternative to --media)
- **Mutually Exclusive:** Cannot use with --media
- **Validation:** Must be valid YouTube URL format
- **Examples:**
  - `--youtube-url "https://youtube.com/watch?v=VIDEO_ID"`
  - `--youtube-url "https://youtu.be/VIDEO_ID"`
  - `--youtube-url "https://youtube.com/shorts/VIDEO_ID"`

### Usage Examples

**Basic Transcription:**
```bash
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow transcribe \
  --source-language en
```

**Translation:**
```bash
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow translate \
  --source-language hi \
  --target-language en
```

**Subtitles:**
```bash
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es
```

### Error Messages

**Invalid URL:**
```
[ERROR] Invalid YouTube URL format
Supported formats:
  - https://youtube.com/watch?v=VIDEO_ID
  - https://youtu.be/VIDEO_ID
  - https://youtube.com/shorts/VIDEO_ID
```

**Video Unavailable:**
```
[ERROR] YouTube video not available
Possible reasons:
  - Video is private or deleted
  - Video is region-restricted
  - Network connectivity issue
```

**Timeout:**
```
[ERROR] Download timed out after 30 minutes
Try:
  - Increase YOUTUBE_DOWNLOAD_TIMEOUT in config
  - Check network connection
  - Use lower quality setting
```

---

## VI. Output Format Requirements

### Downloaded Files

**Location:** `in/youtube/{sanitized_title}.mp4`

**Naming Convention:**
- Original title: "Jaane Tu Ya Jaane Na | Full Movie | Hindi"
- Sanitized: "Jaane_Tu_Ya_Jaane_Na_Full_Movie_Hindi.mp4"
- Rules:
  - Remove special characters: <>:"/\|?*
  - Replace spaces with underscores
  - Limit to 200 characters
  - Preserve original extension (.mp4, .m4a, .webm)

**Format Specifications:**
- **Container:** MP4 (preferred) or best available
- **Video Codec:** H.264 (preferred) or H.265
- **Audio Codec:** AAC or Opus
- **Quality:** As specified (default: best)
- **Metadata:** Preserved from YouTube

### Pipeline Outputs

**No changes to existing output formats:**
- Transcribe: `.txt` file (same as local files)
- Translate: `.txt` file (same as local files)
- Subtitle: `.mp4` with embedded `.srt`/`.vtt` (same as local files)

---

## VII. Non-Functional Requirements

### Performance

**Download Performance:**
- ✅ Typical video (<100MB): <5 minutes
- ✅ Large video (500MB): <15 minutes
- ✅ Full movie (2GB): <30 minutes
- ✅ Progress reporting every 5 seconds
- ✅ Network efficiency: resume capability (Phase 2)

**Pipeline Performance:**
- ✅ No degradation vs. local files
- ✅ Same ASR/translation/subtitle quality
- ✅ Same processing times

### Compatibility

**YouTube Formats:**
- ✅ Standard videos (youtube.com/watch)
- ✅ Short URLs (youtu.be)
- ✅ Shorts (youtube.com/shorts)
- ❌ Live streams (Phase 2)
- ❌ Playlists (Phase 2)

**Operating Systems:**
- ✅ macOS (Apple Silicon + Intel)
- ✅ Linux (Ubuntu 20.04+)
- ✅ Windows (via WSL2)

**Python Versions:**
- ✅ Python 3.11+
- ✅ yt-dlp 2024.8.6+

### Scalability

**Single Job:**
- ✅ Videos up to 3 hours (full movies)
- ✅ File sizes up to 5GB
- ✅ Any quality available on YouTube

**Concurrent Jobs:**
- ✅ Multiple jobs can download simultaneously
- ✅ Configurable concurrent download limit
- ✅ Cache prevents duplicate downloads

**Storage:**
- ✅ Configurable cache size limit
- ✅ Automatic cache cleanup (oldest first)
- ✅ Manual cache clear command

### Reliability

**Error Handling:**
- ✅ Network timeout: retry with exponential backoff
- ✅ Partial download: cleanup temp files
- ✅ Invalid format: clear error message
- ✅ Authentication failure: secure error (no credential leak)

**Logging:**
- ✅ Download progress logged
- ✅ File size and duration logged
- ✅ Error details logged (exc_info=True)
- ✅ Never log credentials

---

## VIII. Dependencies & Constraints

### Technical Dependencies

**Required Libraries:**
```
yt-dlp>=2024.8.6
```

**Optional Dependencies:**
- FFmpeg (for format conversion) - already required
- Python 3.11+ - already required

### Configuration Parameters

**New Parameters in `config/.env.pipeline`:**

```bash
# YouTube Integration
YOUTUBE_ENABLED=true
YOUTUBE_QUALITY=best  # best, 1080p, 720p, 480p, audio_only
YOUTUBE_USERNAME=  # Optional, for premium/private videos
YOUTUBE_PASSWORD=  # Optional, for premium/private videos
YOUTUBE_DOWNLOAD_TIMEOUT=1800  # 30 minutes default
YOUTUBE_CACHE_DIR=in/youtube/.ytdl-cache
YOUTUBE_MAX_CACHE_SIZE_GB=50  # Max cache size
```

### Business Constraints

**Timeline:**
- Phase 1 (MVP): 1 week
- Phase 2 (Enhancements): 2 weeks
- Total: 3 weeks

**Budget:**
- Development: 40 hours
- Testing: 10 hours
- Documentation: 10 hours
- Total: 60 hours

### Risk Factors

**Technical Risks:**
- yt-dlp API changes (Mitigation: Pin version, monitor repo)
- YouTube rate limiting (Mitigation: Authentication, backoff)
- Format incompatibility (Mitigation: Smart format selection)

**Business Risks:**
- Copyright concerns (Mitigation: User responsibility disclaimer)
- YouTube ToS changes (Mitigation: Monitor ToS, adapt as needed)

---

## IX. Success Criteria

### Definition of Done

**Code Complete:**
- [ ] youtube_downloader.py implemented
- [ ] prepare-job.sh integration complete
- [ ] Configuration parameters added
- [ ] Requirements updated
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Compliance checks passing (100%)

**Testing Complete:**
- [ ] Public video download verified
- [ ] Premium account authentication verified
- [ ] All three workflows tested
- [ ] Error handling validated
- [ ] Performance benchmarks met

**Documentation Complete:**
- [ ] README.md updated with examples
- [ ] Workflow guide updated
- [ ] Troubleshooting guide created
- [ ] Configuration reference updated
- [ ] User guide published

**Acceptance:**
- [ ] Product owner approval
- [ ] Stakeholder demo completed
- [ ] Early adopter feedback positive
- [ ] No critical bugs

---

## X. Analytics & Tracking

### Event Tracking

**Download Events:**
- `youtube_download_started` (video_id, quality)
- `youtube_download_completed` (video_id, duration, file_size)
- `youtube_download_failed` (video_id, error_type)

**Workflow Events:**
- `youtube_transcribe_workflow` (video_id)
- `youtube_translate_workflow` (video_id, source_lang, target_lang)
- `youtube_subtitle_workflow` (video_id, target_languages)

### Success Metrics

**Adoption Metrics:**
- 50%+ of new jobs use YouTube URLs (Month 1)
- 70%+ of YouTube jobs complete successfully
- 20%+ of users use premium authentication

**Performance Metrics:**
- 95%+ download success rate (public videos)
- <5 min average download time
- No quality degradation vs. local files

**Quality Metrics:**
- ASR WER maintained (≤5% for English, ≤15% for Hindi)
- Translation BLEU maintained (≥90%)
- Subtitle quality maintained (≥88%)

---

## XI. Appendix

### Related Documents

**BRD:**
- [BRD-2025-12-10-02-youtube-integration.md](../brd/BRD-2025-12-10-02-youtube-integration.md)

**TRD:**
- [TRD-2025-12-10-02-youtube-integration.md](../trd/TRD-2025-12-10-02-youtube-integration.md) (Next)

**Implementation:**
- [IMPLEMENTATION_TRACKER.md](../../../IMPLEMENTATION_TRACKER.md) - Task T-XXX

### Open Questions

1. ❓ Should we support 4K downloads (requires more storage)?
   - **Decision:** Phase 2 - add if requested by users

2. ❓ Should we extract YouTube metadata (title, description, tags)?
   - **Decision:** Phase 2 - useful for TMDB enrichment

3. ❓ Should we support YouTube playlists in Phase 1?
   - **Decision:** No - defer to Phase 2 for complexity

4. ❓ Should we provide progress bar in terminal?
   - **Decision:** Yes - use yt-dlp's built-in progress

### Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-10 | Initial PRD | Product Team |

---

**Document Status:** ✅ Ready for TRD and Implementation  
**Next Steps:**
1. Create TRD-2025-12-10-02-youtube-integration.md
2. Implement youtube_downloader.py
3. Update prepare-job.sh
4. Add tests and documentation
