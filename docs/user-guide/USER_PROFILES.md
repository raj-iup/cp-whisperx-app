# User Profile System Guide

**Version:** 2.0 | **Status:** Production Ready | **Date:** 2025-12-10

Complete guide to the userId-based user profile system for managing credentials and multi-user support.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Profile Structure](#profile-structure)
4. [Managing Credentials](#managing-credentials)
5. [Workflow Requirements](#workflow-requirements)
6. [Multi-User Support](#multi-user-support)
7. [Troubleshooting](#troubleshooting)
8. [Migration from Legacy](#migration-from-legacy)

---

## Overview

The User Profile System provides:

- **Centralized Credential Storage**: All API keys in one place per user
- **Multi-User Support**: Multiple users can use the same system (users/1/, users/2/, etc.)
- **Workflow Validation**: Automatically validates required credentials before job execution
- **Future-Ready**: Database-backed profiles coming in future releases
- **Backward Compatible**: Works with existing `config/secrets.json` (auto-migrated)

**Directory Structure:**
```
users/
├── 1/
│   ├── profile.json      ← User 1's credentials and preferences
│   └── cache/            ← User 1's cache (ML models, fingerprints)
├── 2/                    ← User 2 (if created)
│   ├── profile.json
│   └── cache/
└── .userIdCounter        ← Tracks next userId (auto-increment)
```

---

## Quick Start

### First-Time Setup

**Step 1: Bootstrap** (creates userId=1 automatically)
```bash
./bootstrap.sh
```

Output:
```
✓ Creating user profile directory: users/1/
✓ Migrating config/secrets.json to users/1/profile.json
✓ User profile created: userId=1
```

**Step 2: Add Your Credentials**
```bash
# Edit profile
nano users/1/profile.json
```

Add required credentials:
```json
{
  "user_id": 1,
  "name": "Your Name",
  "email": "you@example.com",
  "created_at": "2025-12-10T19:00:00Z",
  "updated_at": "2025-12-10T19:00:00Z",
  "credentials": {
    "huggingface": {
      "token": "hf_your_token_here"
    },
    "tmdb": {
      "api_key": "your_tmdb_api_key_here"
    },
    "openai": {
      "api_key": "sk-your_openai_key_here"
    }
  }
}
```

**Step 3: Validate Profile**
```bash
./prepare-job.sh --media in/test.mp4 --workflow subtitle \
  --source-language hi --target-language en

# Output:
# 👤 Validating user profile...
# ✓ User profile loaded: userId=1
# ✓ Credentials validated for subtitle workflow
# ✅ Job preparation complete!
```

---

## Profile Structure

### profile.json Schema

```json
{
  "user_id": 1,                          // Unique user identifier
  "name": "John Doe",                    // Display name (optional)
  "email": "john@example.com",           // Email (optional)
  "created_at": "2025-12-10T19:00:00Z", // Creation timestamp
  "updated_at": "2025-12-10T19:00:00Z", // Last update timestamp
  
  "credentials": {
    // HuggingFace (REQUIRED for all workflows)
    "huggingface": {
      "token": "hf_..."               // Required for WhisperX, PyAnnote
    },
    
    // TMDB (REQUIRED for subtitle workflow with movies)
    "tmdb": {
      "api_key": "..."                // Required for cast/crew metadata
    },
    
    // AI Providers (OPTIONAL - for AI summarization)
    "openai": {
      "api_key": "sk-...",            // For GPT-3.5/4 summarization
      "model": "gpt-4"                // Optional model override
    },
    "anthropic": {
      "api_key": "sk-ant-...",        // For Claude summarization
      "model": "claude-3-opus"        // Optional model override
    },
    "google": {
      "api_key": "...",               // For Gemini summarization
      "model": "gemini-pro"           // Optional model override
    }
  },
  
  "preferences": {
    "default_source_language": "en",   // Optional defaults
    "default_target_languages": ["hi", "es"],
    "enable_ai_summarization": false
  }
}
```

---

## Managing Credentials

### Adding Credentials

**Method 1: Manual Edit**
```bash
nano users/1/profile.json
# Add credentials to "credentials" section
```

**Method 2: Python API**
```python
from shared.user_profile import UserProfile

profile = UserProfile.load(user_id=1)
profile.set_credential('openai', 'api_key', 'sk-...')
profile.save()
```

### Getting Credentials

**In Python:**
```python
from shared.user_profile import UserProfile

profile = UserProfile.load(user_id=1)
hf_token = profile.get_credential('huggingface', 'token')
tmdb_key = profile.get_credential('tmdb', 'api_key')
openai_key = profile.get_credential('openai', 'api_key')
```

**In Shell Scripts:**
```bash
# Credentials are loaded by prepare-job.sh automatically
# Validated before job creation
```

### Removing Credentials

**Option 1: Set to null**
```json
{
  "credentials": {
    "openai": {
      "api_key": null
    }
  }
}
```

**Option 2: Delete entire service**
```json
{
  "credentials": {
    // Don't include service at all
  }
}
```

---

## Workflow Requirements

### Transcribe Workflow

**Required Credentials:**
- ✅ `huggingface.token` - For WhisperX ASR

**Optional:**
- None

**Example:**
```bash
./prepare-job.sh --media in/audio.mp4 --workflow transcribe -s en
```

### Translate Workflow

**Required Credentials:**
- ✅ `huggingface.token` - For WhisperX ASR
- ✅ Source language must be Indian language (hi, ta, te, etc.)

**Optional:**
- None

**Example:**
```bash
./prepare-job.sh --media in/audio.mp4 --workflow translate -s hi -t en
```

### Subtitle Workflow

**Required Credentials:**
- ✅ `huggingface.token` - For WhisperX, PyAnnote
- ✅ `tmdb.api_key` - For movie metadata (if movie content)

**Optional:**
- `openai.api_key` - For AI summarization (if enabled)
- `anthropic.api_key` - Alternative AI provider
- `google.api_key` - Alternative AI provider

**Example:**
```bash
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu,ta
```

---

## Multi-User Support

### Creating Additional Users

**Option 1: Bootstrap (Automatic)**
```bash
# First user already created (userId=1)
# Future: ./bootstrap.sh --user "New User" --email "new@example.com"
```

**Option 2: Python API**
```python
from shared.user_profile import UserProfile

# Create new user
user_id = UserProfile.create_new_user(
    name="Jane Doe",
    email="jane@example.com",
    hf_token="hf_...",
    tmdb_api_key="..."
)
print(f"Created userId={user_id}")
```

### Using Specific User

```bash
# Prepare job for specific user
./prepare-job.sh --media in/test.mp4 --workflow subtitle \
  --user-id 2  # Use userId=2's credentials
```

### Switching Users

```bash
# User 1's job
./prepare-job.sh --media in/file.mp4 --workflow subtitle --user-id 1

# User 2's job
./prepare-job.sh --media in/file.mp4 --workflow subtitle --user-id 2
```

Each user's credentials are isolated and secure.

---

## Troubleshooting

### Common Issues

#### Issue 1: "User profile not found"

**Error:**
```
❌ User profile not found: userId=1
```

**Solution:**
```bash
# Run bootstrap to create default user
./bootstrap.sh

# Or create user manually
mkdir -p users/1
cat > users/1/profile.json << 'EOF'
{
  "user_id": 1,
  "name": "Default User",
  "email": "",
  "created_at": "2025-12-10T19:00:00Z",
  "updated_at": "2025-12-10T19:00:00Z",
  "credentials": {}
}
EOF
```

#### Issue 2: "Missing required credential"

**Error:**
```
❌ Missing required credential: huggingface.token
```

**Solution:**
```bash
# Add token to profile
nano users/1/profile.json

# Add under "credentials":
"huggingface": {
  "token": "hf_your_token_here"
}
```

**Get HuggingFace Token:**
1. Visit https://huggingface.co/settings/tokens
2. Create "Read" access token
3. Copy token to profile

#### Issue 3: "TMDB API key not found"

**Error:**
```
❌ Missing required credential: tmdb.api_key
```

**Solution (Subtitle Workflow Only):**
```bash
# Add TMDB key to profile
nano users/1/profile.json

# Add under "credentials":
"tmdb": {
  "api_key": "your_tmdb_api_key"
}
```

**Get TMDB API Key:**
1. Visit https://www.themoviedb.org/settings/api
2. Request API key
3. Copy API Key (v3 auth) to profile

#### Issue 4: Invalid JSON

**Error:**
```
❌ Failed to load profile: JSON decode error
```

**Solution:**
```bash
# Validate JSON syntax
python3 -m json.tool users/1/profile.json

# Fix common issues:
# - Missing commas
# - Trailing commas (not allowed)
# - Unquoted strings
# - Unclosed braces
```

#### Issue 5: Profile permissions

**Error:**
```
❌ Permission denied: users/1/profile.json
```

**Solution:**
```bash
# Fix permissions
chmod 600 users/1/profile.json  # Owner read/write only
chown $USER users/1/profile.json
```

### Validation Commands

**Check profile exists:**
```bash
ls -la users/1/profile.json
```

**Validate JSON:**
```bash
python3 -m json.tool users/1/profile.json
```

**Test profile loading:**
```python
from shared.user_profile import UserProfile
profile = UserProfile.load(user_id=1)
print(f"✓ Profile loaded: {profile.name}")
print(f"✓ Credentials: {list(profile.data['credentials'].keys())}")
```

**Validate for workflow:**
```python
from shared.user_profile import UserProfile
profile = UserProfile.load(user_id=1)
profile.validate_for_workflow('subtitle')  # Raises error if missing credentials
print("✓ All required credentials present")
```

---

## Migration from Legacy

### Automatic Migration

When you run `./bootstrap.sh`, it automatically migrates `config/secrets.json` to `users/1/profile.json`.

**Before (config/secrets.json):**
```json
{
  "hf_token": "hf_...",
  "tmdb_api_key": "...",
  "openai_api_key": "sk-..."
}
```

**After (users/1/profile.json):**
```json
{
  "user_id": 1,
  "name": "Default User",
  "email": "",
  "created_at": "2025-12-10T19:00:00Z",
  "updated_at": "2025-12-10T19:00:00Z",
  "credentials": {
    "huggingface": {
      "token": "hf_..."
    },
    "tmdb": {
      "api_key": "..."
    },
    "openai": {
      "api_key": "sk-..."
    }
  }
}
```

### Manual Migration

If bootstrap didn't run or you want to migrate manually:

```bash
# Backup old secrets
cp config/secrets.json config/secrets.json.backup

# Create profile directory
mkdir -p users/1

# Python migration script
python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime

# Load old secrets
secrets_path = Path("config/secrets.json")
if secrets_path.exists():
    with open(secrets_path) as f:
        secrets = json.load(f)
    
    # Create new profile
    profile = {
        "user_id": 1,
        "name": "Default User",
        "email": "",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "credentials": {
            "huggingface": {
                "token": secrets.get("hf_token", "")
            },
            "tmdb": {
                "api_key": secrets.get("tmdb_api_key", "")
            },
            "openai": {
                "api_key": secrets.get("openai_api_key", "")
            },
            "anthropic": {
                "api_key": secrets.get("anthropic_api_key", "")
            }
        }
    }
    
    # Remove empty credentials
    profile["credentials"] = {k: v for k, v in profile["credentials"].items() if any(v.values())}
    
    # Save profile
    profile_path = Path("users/1/profile.json")
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)
    
    print(f"✓ Migrated to: {profile_path}")
else:
    print("❌ No secrets.json found")
EOF

# Initialize counter
echo "2" > users/.userIdCounter
```

---

## Best Practices

### Security

1. **File Permissions**
   ```bash
   chmod 600 users/*/profile.json  # Owner read/write only
   ```

2. **Never Commit**
   ```bash
   # Already in .gitignore
   users/
   ```

3. **Backup**
   ```bash
   # Regular backups
   cp -r users/ backups/users-$(date +%Y%m%d)/
   ```

### Organization

1. **One Profile Per Person**
   - userId=1: Personal account
   - userId=2: Work account
   - userId=3: Team member

2. **Meaningful Names**
   ```json
   {
     "name": "John Doe (Personal)",
     "email": "john.doe@personal.com"
   }
   ```

3. **Credential Rotation**
   - Rotate API keys regularly
   - Update profile.json
   - Old jobs still work (credentials snapshot in job.json)

---

## Advanced Usage

### Python API

Complete API reference:

```python
from shared.user_profile import UserProfile, UserIdManager

# === User Management ===

# Create new user
user_id = UserProfile.create_new_user(
    name="Jane Doe",
    email="jane@example.com",
    hf_token="hf_...",
    tmdb_api_key="...",
    openai_api_key="sk-..."
)

# Load existing user
profile = UserProfile.load(user_id=1)

# Check if user exists
exists = UserIdManager.user_exists(1)

# Get next userId
next_id = UserIdManager.get_next_user_id()

# === Credential Management ===

# Get credential
token = profile.get_credential('huggingface', 'token')
api_key = profile.get_credential('tmdb', 'api_key')

# Set credential
profile.set_credential('openai', 'api_key', 'sk-...')
profile.set_credential('openai', 'model', 'gpt-4')

# Save changes
profile.save()

# === Validation ===

# Validate for specific workflow
try:
    profile.validate_for_workflow('subtitle')
    print("✓ All required credentials present")
except ValueError as e:
    print(f"❌ Missing credentials: {e}")

# === Preferences ===

# Get preference
lang = profile.get_preference('default_source_language', 'en')

# Set preference
profile.set_preference('enable_ai_summarization', True)
profile.save()
```

---

## Future Enhancements

### Planned Features (Not Yet Implemented)

**Phase 8: Database Backend**
- SQLite/PostgreSQL support
- Remote profile storage
- Multi-machine synchronization

**Phase 9: Enhanced Security**
- Credential encryption at rest
- OS keychain integration (macOS Keychain, Windows Credential Manager)
- OAuth2 support for services

**Phase 10: Team Features**
- Organization/team profiles
- Role-based access control
- Shared credential vaults
- Audit logging

**Phase 11: Web UI**
- Web-based profile management
- Credential rotation reminders
- Usage analytics

---

## References

- **Architecture:** [USER_PROFILE_ARCHITECTURE_V2.md](../../USER_PROFILE_ARCHITECTURE_V2.md)
- **BRD:** [BRD-2025-12-10-05-user-profile-management.md](../requirements/brd/BRD-2025-12-10-05-user-profile-management.md)
- **PRD:** [PRD-2025-12-10-05-user-profile-management.md](../requirements/prd/PRD-2025-12-10-05-user-profile-management.md)
- **TRD:** [TRD-2025-12-10-05-user-profile-management.md](../requirements/trd/TRD-2025-12-10-05-user-profile-management.md)
- **Implementation Status:** [USER_PROFILE_V2_IMPLEMENTATION_STATUS.md](../../USER_PROFILE_V2_IMPLEMENTATION_STATUS.md)
- **Developer Guide:** [DEVELOPER_STANDARDS.md](../developer/DEVELOPER_STANDARDS.md)

---

**Questions?** Check [troubleshooting.md](troubleshooting.md) or open an issue.
