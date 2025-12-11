# YouTube Premium Setup Guide

**Phase 1 Requirement:** YouTube Premium account required for video downloads.

---

## Why YouTube Premium?

For Phase 1, we require YouTube Premium to ensure:
- ✅ Legal compliance (Premium allows offline downloads)
- ✅ Higher quality video access
- ✅ No rate limiting issues
- ✅ Access to Premium-only content

---

## Setup Instructions

### Step 1: Get YouTube Premium

If you don't have YouTube Premium:
1. Go to: https://www.youtube.com/premium
2. Subscribe to YouTube Premium
3. Note your login credentials (email/password)

### Step 2: Add Credentials to User Profile

Edit your user profile: `users/{userId}/profile.json`

```json
{
  "userId": 1,
  "online_services": {
    "youtube": {
      "premium": {
        "username": "your-email@gmail.com",
        "password": "your-youtube-password",
        "enabled": true
      }
    }
  }
}
```

**Important:**
- Use your YouTube/Google account email
- Use your account password (or app-specific password if 2FA enabled)
- Set `enabled: true` to activate

### Step 3: Test Authentication

```bash
# Test download with your credentials
python3 shared/online_downloader.py "https://youtube.com/watch?v=VIDEO_ID"
```

You should see:
```
✅ Loaded YouTube Premium credentials for user 1
⬇️  Downloading from YouTube...
   Authentication: YouTube Premium (user: your-email@gmail.com)
   Using YouTube Premium credentials
```

---

## Security Best Practices

### 1. Use App-Specific Password (Recommended)

If you have 2FA enabled (recommended):

1. Go to: https://myaccount.google.com/apppasswords
2. Create new app password for "Other (Custom name)" → "CP-WhisperX"
3. Use the generated password in profile.json

```json
{
  "premium": {
    "username": "your-email@gmail.com",
    "password": "xxxx xxxx xxxx xxxx",  // App-specific password
    "enabled": true
  }
}
```

### 2. Protect Your Profile File

```bash
# Restrict file permissions (Linux/macOS)
chmod 600 users/{userId}/profile.json

# Keep profile out of version control
echo "users/*/profile.json" >> .gitignore
```

### 3. Environment Variables (Alternative)

Instead of storing in profile, use environment variables:

```bash
# Set in your shell profile (~/.bashrc or ~/.zshrc)
export YOUTUBE_USERNAME="your-email@gmail.com"
export YOUTUBE_PASSWORD="your-password"
```

Then the downloader will automatically pick them up.

---

## Troubleshooting

### Error: "Login failed"

**Causes:**
1. Incorrect username/password
2. 2FA enabled without app-specific password
3. Account locked/suspended

**Solutions:**
1. Verify credentials are correct
2. Create app-specific password if 2FA enabled
3. Check YouTube account status

### Error: "YouTube Premium required"

**Cause:** Account doesn't have active Premium subscription

**Solution:** Subscribe to YouTube Premium or use public videos only

### Error: "Rate limiting"

**Cause:** Too many download requests

**Solution:** 
- Wait a few minutes before retrying
- YouTube Premium reduces rate limiting

---

## Usage Examples

### Basic Download (with Premium)

```python
from shared.online_downloader import OnlineMediaDownloader, load_youtube_credentials

# Load credentials from user profile
username, password = load_youtube_credentials(user_id=1)

# Create downloader with authentication
downloader = OnlineMediaDownloader(
    youtube_username=username,
    youtube_password=password
)

# Download video
local_path, metadata = downloader.download("https://youtube.com/watch?v=VIDEO_ID")
print(f"Downloaded: {local_path}")
```

### Pipeline Usage

```bash
# Prepare job with YouTube URL (credentials loaded automatically)
./prepare-job.sh --media "https://youtube.com/watch?v=VIDEO_ID" --workflow transcribe

# Run pipeline
./run-pipeline.sh --job-dir out/latest
```

---

## FAQ

### Q: Do I need YouTube Premium for every user?

**A:** Each user needs their own YouTube Premium account if they want to download videos.

### Q: Can I share credentials between users?

**A:** Technically yes, but not recommended. Each user should have their own account.

### Q: What if I don't have YouTube Premium?

**A:** Phase 1 requires Premium. Phase 2+ will support public video downloads without Premium.

### Q: Is this legal?

**A:** Yes. YouTube Premium explicitly allows offline downloads. We're using official YouTube Premium features via yt-dlp.

### Q: Can I use this for commercial purposes?

**A:** Check YouTube's Terms of Service and your Premium subscription terms.

---

## Configuration Reference

### Full Profile Structure

```json
{
  "userId": 1,
  "version": "1.0",
  "user": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "online_services": {
    "youtube": {
      "api_key": "",           // For future YouTube Data API features
      "enabled": true,          // Enable YouTube service
      "premium": {
        "username": "your-email@gmail.com",
        "password": "your-password-or-app-password",
        "enabled": true         // Enable Premium authentication
      }
    }
  }
}
```

### Environment Variables (Alternative)

```bash
# YouTube Premium credentials
export YOUTUBE_USERNAME="your-email@gmail.com"
export YOUTUBE_PASSWORD="your-password"

# Or load from file
source ~/.youtube_credentials
```

---

## Support

For issues:
1. Check credentials are correct in `users/{userId}/profile.json`
2. Verify YouTube Premium subscription is active
3. Try app-specific password if 2FA enabled
4. Check logs: `logs/online_downloader.log`

---

**Last Updated:** 2025-12-10  
**Phase:** 1 (YouTube Premium Required)  
**Status:** Production Ready
