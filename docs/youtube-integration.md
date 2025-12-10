# YouTube Integration Guide

**Version:** 1.0  
**Status:** ✅ Complete (Phase 5, Week 3)  
**Related:** PRD-2025-12-10-02, TRD-2025-12-10-02

## Overview

CP-WhisperX now supports downloading videos directly from YouTube URLs. The integration is **seamless and transparent** - just pass a YouTube URL to `--media` and the system handles the rest.

---

## ✨ Features

### **1. Seamless Integration**
- Pass YouTube URL directly to `prepare-job.sh`
- Auto-downloads before pipeline execution
- Pipeline stages process local file (URL-agnostic)

### **2. Smart Caching**
- Downloads to `in/online/` directory
- Reuses cached files (by video_id)
- Saves bandwidth and time on repeated runs

### **3. YouTube Premium Support**
- Auto-detects credentials from user profile
- Better quality and no ads (optional)
- Configured per user

### **4. Filename Sanitization**
- Format: `{sanitized_title}_{video_id}.mp4`
- Title truncated to 35 characters (alphanumeric + underscore only)
- Video ID suffix ensures uniqueness

---

## 🚀 Quick Start

### **Example 1: Transcribe YouTube Video**
```bash
./prepare-job.sh \
  --media "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow transcribe \
  --source-language en
```

### **Example 2: Multi-Language Subtitles**
```bash
./prepare-job.sh \
  --media "https://youtu.be/VIDEO_ID" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta
```

### **Example 3: Translate Workflow**
```bash
./prepare-job.sh \
  --media "https://youtube.com/watch?v=VIDEO_ID" \
  --workflow translate \
  --source-language hi \
  --target-language en
```

---

## 📁 File Structure

### **Downloaded Files Location**
```
in/
└── online/                                  # YouTube downloads
    ├── Never_Gonna_Give_You_Up_dQw4w9WgXcQ.mp4
    ├── Energy_Demand_in_AI_abc123xyz.mp4
    └── ...
```

### **Cache Behavior**
```bash
# First run (download)
$ ./prepare-job.sh --media "https://youtu.be/VIDEO_ID" --workflow transcribe -s en
🌐 Online URL detected: https://youtu.be/VIDEO_ID
⬇️  Downloading video to in/online/...
   Progress: 45% | Speed: 2.1 MB/s | ETA: 00:15
✅ Video ready: in/online/Video_Title_VIDEO_ID.mp4

# Second run (cache hit)
$ ./prepare-job.sh --media "https://youtu.be/VIDEO_ID" --workflow subtitle -s hi -t en
🌐 Online URL detected: https://youtu.be/VIDEO_ID
⬇️  Downloading video to in/online/...
✅ Found cached video: Video_Title_VIDEO_ID.mp4
♻️  Using cached video (skip download)
✅ Video ready: in/online/Video_Title_VIDEO_ID.mp4
```

---

## 🔧 Configuration

### **YouTube Premium Credentials (Optional)**

Configure YouTube Premium in user profile for better quality:

```bash
# Edit user profile
vim users/1/profile.json
```

```json
{
  "user_id": 1,
  "online_services": {
    "youtube": {
      "premium": {
        "enabled": true,
        "username": "your_email@gmail.com",
        "password": "your_password"
      }
    }
  }
}
```

**Benefits:**
- Higher quality downloads (up to 4K)
- No advertisements
- Access to premium-only content

---

## 🎯 Architecture

### **Download Flow**

```
User → prepare-job.sh → Detect URL → Download → Cache → job.json → Pipeline
         ↓                    ↓           ↓        ↓         ↓
    --media URL          is_url()?   yt-dlp   in/online/  input_media=local_path
```

### **Key Design Decisions**

1. ✅ **Download in prepare-job.sh** (NOT in pipeline stages)
   - User sees progress immediately
   - Cache check before job creation
   - Simpler Stage 01 logic
   - Clean separation of concerns

2. ✅ **Pipeline stages are URL-agnostic**
   - Stage 01 (demux) only processes local files
   - No URL handling in pipeline
   - `job.json` always contains local path

3. ✅ **Smart caching by video_id**
   - Same video_id = reuse cached file
   - Saves bandwidth and time
   - User notified of cache hits

---

## 📊 Performance

### **Download Times (Approximate)**

| Video Length | Quality | Download Time | Notes |
|--------------|---------|---------------|-------|
| 5 minutes    | 1080p   | 1-2 minutes   | ~100 MB |
| 10 minutes   | 1080p   | 2-4 minutes   | ~200 MB |
| 30 minutes   | 1080p   | 5-10 minutes  | ~600 MB |
| 1 hour       | 1080p   | 10-20 minutes | ~1.2 GB |

**Note:** Times vary based on internet speed and YouTube server load.

### **Cache Benefits**

| Scenario | First Run | Cached Run | Savings |
|----------|-----------|------------|---------|
| Same URL | 5 min download | 0 sec | 100% |
| Different clip, same video | 5 min download | 0 sec | 100% |

---

## 🛠️ Troubleshooting

### **Issue: Download Fails**

```bash
❌ Download failed:
ERROR: Video unavailable
```

**Solutions:**
1. Check if video is public or accessible
2. Verify YouTube URL is correct
3. Try with YouTube Premium credentials (if private/premium content)
4. Check internet connection

---

### **Issue: yt-dlp Not Installed**

```bash
❌ Download failed:
ERROR: yt-dlp not installed
```

**Solution:**
```bash
pip install -r requirements/requirements-youtube.txt
# or
pip install yt-dlp>=2024.8.6
```

---

### **Issue: Slow Download Speed**

**Solutions:**
1. Use YouTube Premium (better servers)
2. Try different time of day (less congestion)
3. Lower quality setting (edit `shared/online_downloader.py`)

---

## 🧪 Testing

### **Unit Tests**
```bash
# Run online_downloader tests
pytest tests/unit/test_online_downloader.py -v

# Coverage: 40% (31/31 tests passing)
```

### **Integration Test**
```bash
# Test URL detection and module integration
./tests/manual/youtube/test-youtube-download.sh

# Expected: All 6 tests pass
```

### **Manual Test (Real Download)**
```bash
# Download a short video
./prepare-job.sh \
  --media "https://youtu.be/VIDEO_ID" \
  --workflow transcribe \
  --source-language en

# Check downloaded file
ls -lh in/online/
```

---

## 📋 Supported URL Formats

✅ **Supported:**
```
https://youtube.com/watch?v=VIDEO_ID
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://youtube.com/embed/VIDEO_ID
https://youtube.com/v/VIDEO_ID
```

❌ **Not Supported (Phase 1):**
```
https://vimeo.com/12345           # Phase 2+
https://dailymotion.com/x12345    # Phase 2+
https://twitch.tv/videos/12345    # Phase 2+
```

---

## 🚀 Future Enhancements (Phase 2+)

- [ ] Multi-platform support (Vimeo, Dailymotion, etc.)
- [ ] Playlist support (download all videos in playlist)
- [ ] Quality selection via CLI flag
- [ ] Audio-only download for transcribe/translate workflows
- [ ] Retry logic with exponential backoff
- [ ] Progress bar in terminal
- [ ] Resume interrupted downloads

---

## 📚 Related Documentation

- **PRD:** `docs/requirements/prd/PRD-2025-12-10-02-online-media-integration.md`
- **TRD:** `docs/requirements/trd/TRD-2025-12-10-02-online-media-integration.md`
- **Implementation:** `shared/online_downloader.py`
- **Tests:** `tests/unit/test_online_downloader.py`
- **User Profile:** `docs/user-guide/user-profile.md` (YouTube Premium setup)

---

## ✅ Status

**Phase 5, Week 3 - COMPLETE**

- ✅ YouTube URL detection in prepare-job.sh
- ✅ Auto-download to in/online/
- ✅ Smart caching by video_id
- ✅ YouTube Premium support
- ✅ 31/31 unit tests passing
- ✅ Integration tests complete
- ✅ Documentation complete

**Next:** Cost tracking integration (Task #20)
