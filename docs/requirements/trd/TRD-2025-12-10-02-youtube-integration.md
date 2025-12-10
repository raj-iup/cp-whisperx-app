# TRD: YouTube Video Integration

**ID:** TRD-2025-12-10-02  
**Created:** 2025-12-10  
**Status:** Draft  
**Related BRD:** [BRD-2025-12-10-02-youtube-integration](../brd/BRD-2025-12-10-02-youtube-integration.md)  
**Related PRD:** [PRD-2025-12-10-02-youtube-integration](../prd/PRD-2025-12-10-02-youtube-integration.md)

---

## Technical Overview

### Summary

Implement YouTube video download capability by integrating `yt-dlp` library into the job preparation phase. When a user provides `--youtube-url` parameter, the system validates the URL, downloads the video to `in/youtube/` directory, and passes the local file path to the existing pipeline. No changes are required to pipeline stages (01-12).

**Architecture Principle:** Add capability without modifying core pipeline (clean integration).

### Approach

**Single Responsibility Design:**
1. **New Component:** `scripts/youtube_downloader.py` - YouTube download logic
2. **Integration Point:** `prepare-job.sh` - Detects YouTube URL, calls downloader
3. **Existing Pipeline:** Unchanged - operates on local file as usual

**Workflow:**
```
User provides --youtube-url
       ↓
prepare-job.sh detects YouTube parameter
       ↓
youtube_downloader.py downloads video
       ↓
Local file path passed to existing pipeline
       ↓
Pipeline stages process normally (no changes)
```

### Key Technologies

**Primary Dependency:**
- **yt-dlp 2024.8.6+**
  - Purpose: YouTube video download
  - License: Unlicense (public domain)
  - Maintained: Yes (active development)
  - Replaces: youtube-dl (deprecated)
  - Features: Format selection, authentication, progress reporting

**Existing Dependencies (No Changes):**
- FFmpeg: Already required (no changes)
- Python 3.11+: Already required (no changes)
- Shared modules: config_loader, logger (reused)

---

## Architecture Changes

### Affected Components

**NEW Components:**
```
scripts/youtube_downloader.py    # Download logic (NEW)
requirements/requirements-youtube.txt    # yt-dlp dependency (NEW)
in/youtube/    # Download cache directory (NEW)
```

**MODIFIED Components:**
```
prepare-job.sh    # Add --youtube-url detection (MODIFIED)
config/.env.pipeline    # Add YouTube configuration (MODIFIED)
```

**UNCHANGED Components:**
```
pipeline/01_demux.py → ... → 12_mux.py    # All stages (UNCHANGED)
shared/config_loader.py    # Reused as-is
shared/logger.py    # Reused as-is
```

### Integration Points

**1. prepare-job.sh Integration:**
```bash
# Detect --youtube-url parameter
if [[ -n "${YOUTUBE_URL:-}" ]]; then
    # Download video using youtube_downloader.py
    DOWNLOADED_FILE=$(python3 scripts/youtube_downloader.py "$YOUTUBE_URL")
    
    # Update MEDIA parameter to point to downloaded file
    MEDIA="$DOWNLOADED_FILE"
fi

# Continue with normal job creation (existing code)
```

**2. Configuration Integration:**
```bash
# config/.env.pipeline (new section)
YOUTUBE_ENABLED=true
YOUTUBE_QUALITY=best
YOUTUBE_USERNAME=
YOUTUBE_PASSWORD=
YOUTUBE_DOWNLOAD_TIMEOUT=1800
```

**3. Pipeline Integration:**
```
Downloaded file → in/youtube/{title}.mp4
                         ↓
                  Passed as --media parameter
                         ↓
                  Pipeline Stage 01 (demux)
                         ↓
                  All stages process normally
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User Input: --youtube-url "https://youtube.com/..."        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ prepare-job.sh: Detect YouTube URL parameter                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ youtube_downloader.py:                                       │
│   1. Validate URL format                                     │
│   2. Load config (quality, authentication)                   │
│   3. Check cache for existing download                       │
│   4. Download via yt-dlp (if not cached)                     │
│   5. Sanitize filename                                       │
│   6. Save to in/youtube/{title}.mp4                          │
│   7. Return local file path                                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ prepare-job.sh: Update MEDIA parameter to local path        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Existing Pipeline: Process local file (no changes)          │
│   Stage 01-12 execute normally                               │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Output: Transcript/Translation/Subtitles (as usual)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

### Decision 1: Library Selection (yt-dlp vs youtube-dl)

**Problem:** Choose YouTube download library

**Options:**
1. **youtube-dl** - ❌ Rejected
   - Reason: Deprecated, slow development, many sites broken
   
2. **yt-dlp** - ✅ Selected
   - Reason: Active fork, better maintained, faster, more features
   - Supports premium accounts
   - Better format selection
   - Active community (100+ contributors)

**Rationale:**
- yt-dlp is the de facto successor to youtube-dl
- Industry standard for Python YouTube downloads
- Regular updates for YouTube API changes
- Better error handling and progress reporting

---

### Decision 2: Integration Point (prepare-job vs Stage 00)

**Problem:** Where to integrate YouTube download?

**Options:**
1. **New Stage 00 (pre-demux)** - ❌ Rejected
   - Reason: Violates stage isolation principle
   - Stages should operate on local files
   - Creates dependency on external service in pipeline
   
2. **prepare-job.sh** - ✅ Selected
   - Reason: Download is part of job preparation, not processing
   - Keeps pipeline focused on local file processing
   - Clean separation of concerns
   - Easier error handling (fail before pipeline starts)

**Rationale:**
- Job preparation = setup phase (download is setup)
- Pipeline = processing phase (operates on local files)
- Maintains existing architecture principles

---

### Decision 3: Cache Strategy

**Problem:** Should we cache downloaded videos?

**Options:**
1. **No caching** - ❌ Rejected
   - Reason: Wastes bandwidth, slow for repeated use
   
2. **Cache with video ID as key** - ✅ Selected
   - Reason: Prevents re-downloading same video
   - Uses video ID (unique, stable identifier)
   - Configurable cache size and expiration

**Rationale:**
- Users often re-process same videos with different settings
- Video ID is stable (won't change)
- Disk space is cheap, bandwidth/time is expensive
- Easy to implement (check if file exists before download)

---

### Decision 4: Authentication Storage

**Problem:** How to store YouTube credentials?

**Options:**
1. **Command-line parameters** - ❌ Rejected
   - Reason: Insecure (visible in process list, shell history)
   
2. **Environment variables** - ❌ Rejected
   - Reason: Can leak via process inspection, logs
   
3. **Config file (config/.env.pipeline)** - ✅ Selected
   - Reason: Already established pattern
   - File permissions control access
   - Never transmitted to us
   - Optional (not required for public videos)

**Rationale:**
- Consistent with existing configuration pattern
- User controls file permissions
- Clear documentation on security implications
- Optional feature (default: no authentication)

---

### Decision 5: Error Handling Strategy

**Problem:** How to handle download failures?

**Options:**
1. **Retry automatically** - ❌ Rejected
   - Reason: May waste time on permanently unavailable videos
   
2. **Fail fast with clear message** - ✅ Selected
   - Reason: User can fix issue (network, URL, permissions)
   - Clear error messages guide troubleshooting
   - Cleanup partial downloads
   - Exit before pipeline starts (no wasted processing)

**Rationale:**
- Download failures are often user-fixable (wrong URL, network)
- Better UX: immediate feedback vs. wasting 30 minutes processing
- Keeps pipeline clean (only starts if input is valid)

---

## Implementation Requirements

### Code Changes

#### New Files

**1. scripts/youtube_downloader.py** (~300 LOC)
```python
#!/usr/bin/env python3
"""
YouTube Video Downloader for CP-WhisperX-App

Responsibilities:
- Validate YouTube URL format
- Download video/audio via yt-dlp
- Handle authentication (optional)
- Manage caching
- Report progress
- Return local file path
"""

# Key Functions:
def validate_youtube_url(url: str) -> bool
def sanitize_filename(title: str) -> str
def download_youtube_video(url, output_dir, quality, username, password, timeout) -> Optional[Path]
def main() -> int
```

**2. requirements/requirements-youtube.txt**
```
yt-dlp>=2024.8.6
```

**3. tests/integration/test_youtube_integration.py** (~200 LOC)
```python
"""Integration tests for YouTube download functionality"""

def test_download_public_video()
def test_download_with_authentication()
def test_invalid_url_handling()
def test_unavailable_video_handling()
def test_quality_selection()
def test_cache_behavior()
```

#### Modified Files

**1. prepare-job.sh** (+30 LOC)
```bash
# Add after argument parsing, before job creation:

# YouTube URL handling
if [[ -n "${YOUTUBE_URL:-}" ]]; then
    log_info "YouTube URL provided: $YOUTUBE_URL"
    
    # Check if YouTube is enabled
    YOUTUBE_ENABLED=$(grep "^YOUTUBE_ENABLED=" config/.env.pipeline | cut -d= -f2)
    if [[ "$YOUTUBE_ENABLED" != "true" ]]; then
        log_error "YouTube integration is disabled in config"
        exit 1
    fi
    
    log_info "Downloading video..."
    
    # Download video
    DOWNLOADED_FILE=$(python3 scripts/youtube_downloader.py "$YOUTUBE_URL" \
        --output-dir "in/youtube" \
        --quality "${YOUTUBE_QUALITY:-best}")
    
    EXIT_CODE=$?
    if [[ $EXIT_CODE -ne 0 ]] || [[ -z "$DOWNLOADED_FILE" ]]; then
        log_error "Failed to download YouTube video (exit code: $EXIT_CODE)"
        exit 1
    fi
    
    log_success "Downloaded: $DOWNLOADED_FILE"
    
    # Update MEDIA parameter to point to downloaded file
    MEDIA="$DOWNLOADED_FILE"
    
    # Validate downloaded file
    if [[ ! -f "$MEDIA" ]]; then
        log_error "Downloaded file not found: $MEDIA"
        exit 1
    fi
fi

# Continue with normal job creation (existing code)
```

**2. config/.env.pipeline** (+15 LOC)
```bash
# Add new section at end of file:

# ============================================================================
# YouTube Integration
# ============================================================================
# Status: ✅ Implemented (v3.1)
# Purpose: Enable direct YouTube video download for all workflows

# Enable YouTube URL support (true/false)
# Default: true
# Impact: Allows --youtube-url parameter in prepare-job.sh
YOUTUBE_ENABLED=true

# Download quality preference
# Options: best, 1080p, 720p, 480p, audio_only
# Default: best
# Impact: Higher quality = larger file size, better accuracy
YOUTUBE_QUALITY=best

# Authentication (optional - for premium/private videos)
# Leave empty for public videos only
# Security: Stored locally, never transmitted
# Format: Your YouTube email or username
YOUTUBE_USERNAME=

# YouTube account password
# Security: Stored locally, never logged
# Note: Use app-specific password if 2FA enabled
YOUTUBE_PASSWORD=

# Download timeout (seconds)
# Default: 1800 (30 minutes)
# Impact: Prevents hanging on large files
# Recommendation: 1800 for most videos, 3600 for full movies
YOUTUBE_DOWNLOAD_TIMEOUT=1800

# Cache directory for downloaded videos
# Default: in/youtube/.ytdl-cache
# Impact: Prevents re-downloading same video
YOUTUBE_CACHE_DIR=in/youtube/.ytdl-cache

# Maximum cache size (GB)
# Default: 50 GB
# Impact: Automatic cleanup when limit reached
YOUTUBE_MAX_CACHE_SIZE_GB=50
```

**3. prepare-job.sh argument parsing** (+10 LOC)
```bash
# Add YouTube URL parameter to argument parser:

while [[ $# -gt 0 ]]; do
    case $1 in
        --youtube-url)
            YOUTUBE_URL="$2"
            shift 2
            ;;
        # ... existing parameters ...
    esac
done

# Validate mutual exclusivity
if [[ -n "${YOUTUBE_URL:-}" ]] && [[ -n "${MEDIA:-}" ]]; then
    log_error "Cannot use both --youtube-url and --media parameters"
    exit 1
fi

if [[ -z "${YOUTUBE_URL:-}" ]] && [[ -z "${MEDIA:-}" ]]; then
    log_error "Must provide either --youtube-url or --media parameter"
    exit 1
fi
```

### Configuration Changes

**No changes to existing configuration parameters.**

**New parameters documented above in config/.env.pipeline.**

### Dependencies

**New Dependency:**
```
# requirements/requirements-youtube.txt
yt-dlp>=2024.8.6
```

**Installation:**
```bash
pip install -r requirements/requirements-youtube.txt
```

**Dependency Check in bootstrap.sh:**
```bash
# Add to bootstrap.sh dependency checks:
check_python_package "yt_dlp" "yt-dlp" "requirements/requirements-youtube.txt"
```

---

## API Specification

### youtube_downloader.py

#### Function: validate_youtube_url()

```python
def validate_youtube_url(url: str) -> bool:
    """
    Validate YouTube URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid YouTube URL, False otherwise
        
    Supported Formats:
        - https://youtube.com/watch?v=VIDEO_ID
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/shorts/VIDEO_ID
    """
```

#### Function: sanitize_filename()

```python
def sanitize_filename(title: str) -> str:
    """
    Sanitize video title for use as filename.
    
    Args:
        title: Original YouTube video title
        
    Returns:
        Sanitized filename (safe for filesystem)
        
    Rules:
        - Remove characters: <>:"/\\|?*
        - Replace spaces with underscores
        - Limit to 200 characters
        - Preserve alphanumeric and basic punctuation
    """
```

#### Function: download_youtube_video()

```python
def download_youtube_video(
    url: str,
    output_dir: Path,
    quality: str = "best",
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 1800
) -> Optional[Path]:
    """
    Download video from YouTube URL.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save downloaded video
        quality: Quality preference (best, 1080p, 720p, 480p, audio_only)
        username: YouTube account username (optional, for premium/private)
        password: YouTube account password (optional)
        timeout: Download timeout in seconds (default: 1800 = 30 min)
        
    Returns:
        Path to downloaded video file, or None if failed
        
    Raises:
        ValueError: Invalid URL format
        TimeoutError: Download exceeded timeout
        ConnectionError: Network issues
        PermissionError: Authentication failed
        
    Side Effects:
        - Creates output_dir if not exists
        - Downloads video to output_dir/{title}.mp4
        - Logs progress every 5 seconds
        - Cleans up partial downloads on failure
    """
```

#### Main Entry Point

```python
def main() -> int:
    """
    Command-line entry point for YouTube downloader.
    
    Usage:
        python3 scripts/youtube_downloader.py URL [OPTIONS]
        
    Arguments:
        url: YouTube video URL (required)
        --output-dir: Output directory (default: in/youtube)
        --quality: Quality preference (default: best)
        
    Returns:
        0 on success, 1 on failure
        
    Stdout:
        Path to downloaded file (on success)
        
    Stderr:
        Error messages (on failure)
    """
```

---

## Testing Requirements

### Unit Tests (≥80% coverage)

**File:** `tests/unit/test_youtube_downloader.py`

```python
def test_validate_youtube_url_valid():
    """Test URL validation with valid formats"""
    assert validate_youtube_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    assert validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert validate_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ")

def test_validate_youtube_url_invalid():
    """Test URL validation with invalid formats"""
    assert not validate_youtube_url("https://example.com/video")
    assert not validate_youtube_url("not a url")
    assert not validate_youtube_url("")

def test_sanitize_filename():
    """Test filename sanitization"""
    assert sanitize_filename("Video: Title!") == "Video_Title"
    assert sanitize_filename("A" * 300) == "A" * 200  # Length limit
    assert sanitize_filename("File<>Name") == "FileName"  # Remove invalid chars

def test_download_youtube_video_mock():
    """Test download function with mocked yt-dlp"""
    # Mock yt-dlp to avoid actual download in unit tests
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_ydl.return_value.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120
        }
        
        result = download_youtube_video(
            "https://youtube.com/watch?v=test",
            Path("test_output")
        )
        
        assert result is not None
        assert result.name.endswith('.mp4')
```

### Integration Tests

**File:** `tests/integration/test_youtube_integration.py`

**Test Scenario 1: Download Public Video**
```python
def test_download_public_video_integration():
    """
    Integration test: Download actual YouTube video
    
    Requires: Network connectivity
    Uses: Short test video (<1MB)
    Cleanup: Removes downloaded file after test
    """
    url = "https://youtube.com/watch?v=test"  # Public test video
    output_dir = Path("test_output")
    
    try:
        result = download_youtube_video(url, output_dir)
        assert result.exists()
        assert result.stat().st_size > 0
    finally:
        if result and result.exists():
            result.unlink()
        output_dir.rmdir()
```

**Test Scenario 2: Transcribe YouTube Video**
```python
def test_transcribe_youtube_workflow():
    """
    End-to-end test: YouTube URL → Transcription
    
    Steps:
        1. Download YouTube video
        2. Run transcribe workflow
        3. Validate transcript output
        4. Check accuracy (WER ≤5%)
    """
    # Test implementation
```

**Test Scenario 3: Invalid URL Handling**
```python
def test_invalid_url_error_handling():
    """Test graceful handling of invalid YouTube URLs"""
    result = download_youtube_video("invalid_url", Path("output"))
    assert result is None  # Should return None, not crash
```

### Functional Tests

**File:** `tests/manual/youtube/test-youtube-workflows.sh`

```bash
#!/usr/bin/env bash
# Manual functional tests for YouTube integration

# Test 1: Basic transcription
echo "Test 1: YouTube transcribe workflow"
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=TEST_ID" \
  --workflow transcribe \
  --source-language en
./run-pipeline.sh <job_dir>

# Test 2: Translation
echo "Test 2: YouTube translate workflow"
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=HINDI_ID" \
  --workflow translate \
  --source-language hi \
  --target-language en
./run-pipeline.sh <job_dir>

# Test 3: Subtitle generation
echo "Test 3: YouTube subtitle workflow"
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=SONG_ID" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu
./run-pipeline.sh <job_dir>

# Test 4: Error handling
echo "Test 4: Invalid URL error handling"
./prepare-job.sh \
  --youtube-url "https://invalid.com/video" \
  --workflow transcribe
# Expected: Clear error message, exit code 1
```

### Performance Tests

**Benchmarks:**

```python
def test_download_performance():
    """
    Performance test: Download speed
    
    Metrics:
        - Small video (<10MB): <2 minutes
        - Medium video (100MB): <5 minutes
        - Large video (500MB): <15 minutes
    """
    
def test_cache_performance():
    """
    Performance test: Cache hit speed
    
    Metrics:
        - First download: Normal speed
        - Second download (cached): <1 second
        - Cache lookup overhead: <100ms
    """
```

---

## Error Handling

### Error Categories

**1. URL Validation Errors**
```
[ERROR] Invalid YouTube URL format
Supported formats:
  - https://youtube.com/watch?v=VIDEO_ID
  - https://youtu.be/VIDEO_ID
  - https://youtube.com/shorts/VIDEO_ID

Exit Code: 1
```

**2. Network Errors**
```
[ERROR] Network connection failed
Details: Connection timed out after 30 seconds
Suggestion: Check internet connection and try again

Exit Code: 1
```

**3. Video Unavailable**
```
[ERROR] YouTube video not available
Possible reasons:
  - Video is private or deleted
  - Video is age-restricted
  - Video is region-restricted
  - Invalid video ID

Exit Code: 1
```

**4. Authentication Errors**
```
[ERROR] YouTube authentication failed
Check credentials in config/.env.pipeline:
  - YOUTUBE_USERNAME
  - YOUTUBE_PASSWORD
Note: Use app-specific password if 2FA enabled

Exit Code: 1
```

**5. Timeout Errors**
```
[ERROR] Download timed out after 30 minutes
File size: 2.5 GB (incomplete)
Suggestions:
  - Increase YOUTUBE_DOWNLOAD_TIMEOUT in config
  - Use lower quality setting (YOUTUBE_QUALITY=720p)
  - Check network speed

Exit Code: 1
```

**6. Storage Errors**
```
[ERROR] Insufficient disk space
Required: 2.5 GB
Available: 1.2 GB
Suggestion: Free up disk space or clean YouTube cache

Exit Code: 1
```

### Error Handling Patterns

```python
# Pattern 1: Validate early, fail fast
if not validate_youtube_url(url):
    logger.error(f"Invalid YouTube URL: {url}")
    return None

# Pattern 2: Specific exception handling
try:
    ydl.download([url])
except yt_dlp.utils.DownloadError as e:
    logger.error(f"Download failed: {e}", exc_info=True)
    return None
except TimeoutError:
    logger.error(f"Download timed out after {timeout} seconds")
    return None

# Pattern 3: Cleanup on failure
try:
    result = download_video()
except Exception:
    # Clean up partial downloads
    if temp_file.exists():
        temp_file.unlink()
    raise

# Pattern 4: User-actionable messages
logger.error(
    "Video unavailable. "
    "If this is a private video, add credentials to config/.env.pipeline"
)
```

---

## Security Considerations

### Credential Storage

**Requirements:**
- ✅ Credentials stored in config/.env.pipeline (local file)
- ✅ File permissions: 600 (user read/write only)
- ✅ Never log credentials
- ✅ Never transmit credentials to us
- ✅ Optional feature (not required for public videos)

**Implementation:**
```python
# Load credentials securely
username = config.get('YOUTUBE_USERNAME')
password = config.get('YOUTUBE_PASSWORD')

# Never log credentials
logger.debug("Authentication: enabled" if username else "disabled")
# NOT: logger.debug(f"Username: {username}")  # WRONG!

# Pass directly to yt-dlp (doesn't log either)
ydl_opts = {
    'username': username,
    'password': password
}
```

### Input Validation

**URL Validation:**
```python
# Validate before using
if not validate_youtube_url(url):
    raise ValueError("Invalid YouTube URL")

# Prevent command injection
# yt-dlp handles URL safely (no shell execution)
```

### Disk Space Management

**Cache Limits:**
```python
def check_cache_size():
    """Enforce maximum cache size"""
    cache_dir = Path(config.get('YOUTUBE_CACHE_DIR'))
    max_size = int(config.get('YOUTUBE_MAX_CACHE_SIZE_GB', 50)) * 1024**3
    
    current_size = sum(f.stat().st_size for f in cache_dir.rglob('*'))
    
    if current_size > max_size:
        # Remove oldest files first
        logger.warning(f"Cache exceeded {max_size/1024**3:.1f} GB, cleaning up...")
        cleanup_old_cache_files(cache_dir, max_size)
```

---

## Documentation Updates

### README.md

**Add YouTube Integration Section:**

```markdown
### YouTube Integration

Process YouTube videos directly without manual download:

**Transcribe YouTube Video:**
```bash
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow transcribe \
  --source-language en
```

**Translate YouTube Content:**
```bash
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow translate \
  --source-language hi \
  --target-language en
```

**Add Subtitles to YouTube Clip:**
```bash
./prepare-job.sh \
  --youtube-url "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta
```

**Premium Account (Optional):**
For private videos or ad-free experience, add credentials to `config/.env.pipeline`:
```bash
YOUTUBE_USERNAME=your_email@example.com
YOUTUBE_PASSWORD=your_password
```
```

### User Guide (New Document)

**File:** `docs/user-guide/youtube-integration.md`

**Sections:**
1. Overview
2. Installation
3. Basic Usage
4. Premium Accounts
5. Quality Settings
6. Caching
7. Troubleshooting
8. Best Practices

### Troubleshooting Guide

**Add to TROUBLESHOOTING.md:**

```markdown
## YouTube Download Issues

### Video Unavailable
**Symptom:** "YouTube video not available"
**Causes:**
- Video is private or deleted
- Video is age-restricted
- Region restrictions

**Solutions:**
- Verify URL in web browser
- Add authentication for private videos
- Use VPN for region restrictions

### Download Timeout
**Symptom:** "Download timed out after 30 minutes"
**Causes:**
- Large file size
- Slow network connection

**Solutions:**
- Increase timeout: `YOUTUBE_DOWNLOAD_TIMEOUT=3600`
- Use lower quality: `YOUTUBE_QUALITY=720p`
- Check network speed

### Authentication Failed
**Symptom:** "YouTube authentication failed"
**Causes:**
- Invalid credentials
- 2FA not configured

**Solutions:**
- Verify credentials in config/.env.pipeline
- Use app-specific password for 2FA accounts
- Test credentials in web browser first
```

---

## Deployment Plan

### Phase 1: MVP (Week 1)

**Day 1-2: Implementation**
- [ ] Create youtube_downloader.py
- [ ] Modify prepare-job.sh
- [ ] Add configuration parameters
- [ ] Add dependencies

**Day 3: Testing**
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing (all workflows)

**Day 4-5: Documentation**
- [ ] README updates
- [ ] User guide
- [ ] Troubleshooting guide
- [ ] Code documentation

### Phase 2: Enhancement (Week 2-3)

**Features:**
- [ ] Quality selection UI
- [ ] Playlist support
- [ ] Resume downloads
- [ ] Advanced caching

### Rollback Plan

**If Issues Arise:**
1. Remove --youtube-url parameter from prepare-job.sh
2. Set YOUTUBE_ENABLED=false in config
3. Document as "temporarily disabled"
4. No pipeline changes needed (feature isolated)

---

## Success Metrics

### Technical Metrics

**Performance:**
- [ ] Download success rate: ≥95% (public videos)
- [ ] Average download time: <5 minutes
- [ ] Cache hit rate: ≥50% (after 1 week)
- [ ] Pipeline quality maintained (no degradation)

**Reliability:**
- [ ] Error handling: 100% graceful failures
- [ ] Credential security: Zero leaks in logs
- [ ] Disk space: Automatic cleanup working
- [ ] Timeout handling: No hanging processes

**Code Quality:**
- [ ] Unit test coverage: ≥80%
- [ ] Integration tests: All passing
- [ ] Compliance checks: 100% passing
- [ ] Documentation: Complete and accurate

---

## Approval & Sign-off

**Technical Approval:**
- [ ] Lead Developer: _____________________ Date: _______
- [ ] Architect: _________________________ Date: _______
- [ ] QA Lead: ___________________________ Date: _______

**Ready for Implementation:**
- [ ] **YES** - All requirements clear, proceed to implementation
- [ ] **NO** - Issues to address: ___________________

---

## Related Documents

**BRD:**
- [BRD-2025-12-10-02-youtube-integration.md](../brd/BRD-2025-12-10-02-youtube-integration.md)

**PRD:**
- [PRD-2025-12-10-02-youtube-integration.md](../prd/PRD-2025-12-10-02-youtube-integration.md)

**Implementation:**
- [IMPLEMENTATION_TRACKER.md](../../../IMPLEMENTATION_TRACKER.md) - Task T-XXX

**Standards:**
- [DEVELOPER_STANDARDS.md](../../DEVELOPER_STANDARDS.md) - § 21 BRD-PRD-TRD Framework
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) - No AD changes required

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-10  
**Implementation Status:** ⏳ Ready for Development
