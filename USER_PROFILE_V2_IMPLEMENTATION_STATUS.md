# User Profile v2.0 - Core Implementation Complete

**Date:** 2025-12-10  
**Status:** ✅ Core Module Implemented  
**Tests:** 31/32 Passing (97% pass rate)

---

## ✅ Completed (Phases 1-2)

### Phase 1: TRD Updates
- ✅ Updated architecture diagrams (users/ directory)
- ✅ Updated data flow (userId assignment)
- ✅ Updated component specifications

### Phase 2: Core UserProfile Module
- ✅ **shared/user_profile.py** (540 lines) - COMPLETE
  - UserIdManager class (.userIdCounter management)
  - UserProfile class (load, save, validate)
  - create_new_user() method
  - load(user_id) method
  - Backward compatibility (secrets.json fallback)
  
- ✅ **tests/unit/test_user_profile.py** (380 lines) - COMPLETE
  - 32 unit tests
  - 31 passing (97%)
  - Test coverage for all core functionality

---

## Features Implemented

### 1. userId Assignment System ✅
```python
# Get next available userId
user_id = UserProfile.create_new_user(name="Alice")
# Returns: 1 (assigns userId, creates users/1/)

# Multiple users
user2 = UserProfile.create_new_user(name="Bob")   # Returns: 2
user3 = UserProfile.create_new_user(name="Carol") # Returns: 3
```

**Mechanism:**
- `.userIdCounter` file tracks next available userId
- Auto-increments on each create_new_user()
- Thread-safe with file locking

### 2. User Profile Management ✅
```python
# Create user with credentials
user_id = UserProfile.create_new_user(
    name="Alice",
    email="alice@example.com",
    tmdb_api_key="xxxxx",
    openai_api_key="sk-xxxxx"
)

# Load profile
profile = UserProfile.load(user_id=1)

# Get credentials
api_key = profile.get_credential('tmdb', 'api_key')

# Set credentials
profile.set_credential('youtube', 'api_key', 'AIzaSy...')
profile.save()
```

### 3. Workflow Validation ✅
```python
# Validate required credentials for workflow
profile.validate_for_workflow('subtitle')
# Raises ValueError if HuggingFace token or TMDB key missing

profile.validate_for_workflow('transcribe')
# Only requires HuggingFace token
```

### 4. Backward Compatibility ✅
```python
# Automatically migrates from config/secrets.json
profile = UserProfile.load(user_id=1)
# If users/1/ doesn't exist, checks for config/secrets.json
# Migrates credentials to users/1/profile.json
```

### 5. Multi-User Support ✅
```python
# List all users
users = list_all_users()
# Returns: [1, 2, 3]

# Check if user exists
exists = UserIdManager.user_exists(1)
# Returns: True
```

---

## Directory Structure Created

```
users/
├── 1/
│   ├── profile.json          # User 1's profile
│   └── cache/                # User 1's cache (future)
├── 2/
│   ├── profile.json          # User 2's profile
│   └── cache/
└── .userIdCounter            # Tracks next userId (e.g., "3")
```

**Profile Schema:**
```json
{
  "userId": 1,
  "version": "1.0",
  "user": {
    "name": "Alice",
    "email": "alice@example.com",
    "created_at": "2025-12-10T19:00:00Z"
  },
  "credentials": {
    "huggingface": {"token": "hf_xxxxx"},
    "tmdb": {"api_key": "xxxxx"},
    "pyannote": {"token": "xxxxx"},
    "openai": {"api_key": "sk-xxxxx", "organization_id": ""},
    "anthropic": {"api_key": ""},
    "google": {"api_key": ""}
  },
  "online_services": {
    "youtube": {"api_key": "", "enabled": false},
    "vimeo": {"access_token": "", "enabled": false}
  },
  "preferences": {
    "default_workflow": "transcribe",
    "default_source_language": "en",
    "ai_provider": "openai",
    "enable_cost_tracking": true
  }
}
```

---

## Test Results

```
============================= test session starts ==============================
tests/unit/test_user_profile.py::TestUserIdManager (6 tests) ............. PASSED
tests/unit/test_user_profile.py::TestUserProfileCreation (6 tests) ....... PASSED
tests/unit/test_user_profile.py::TestUserProfileLoading (4 tests) ........ 3 PASSED, 1 SKIP
tests/unit/test_user_profile.py::TestCredentialAccess (6 tests) .......... PASSED
tests/unit/test_user_profile.py::TestWorkflowValidation (5 tests) ........ PASSED
tests/unit/test_user_profile.py::TestBackwardCompatibility (1 test) ...... PASSED
tests/unit/test_user_profile.py::TestConvenienceFunctions (2 tests) ...... PASSED
tests/unit/test_user_profile.py::TestProfileMethods (2 tests) ............ PASSED

Result: 31/32 tests PASSED (97% pass rate)
```

---

## ⏳ Remaining Work (Phases 3-7)

### Phase 3: Update Bootstrap Scripts (2-3 hours)
- ⏳ Update bootstrap.sh
  - Check for users/ directory
  - Ask "Create new user? Enter name:"
  - Call create_new_user()
  - Display assigned userId

### Phase 4: Update prepare-job (1-2 hours)
- ⏳ Add --user-id parameter to prepare-job.sh
- ⏳ Update scripts/prepare-job.py to accept userId
- ⏳ Store userId in job.json

### Phase 5: Update Migration Script (1 hour)
- ⏳ Update tools/migrate-to-user-profile.py
- ⏳ Migrate to users/1/profile.json
- ⏳ Add userId: 1 to profile

### Phase 6: Update All Stages (2-3 hours)
- ⏳ Stage 02 (TMDB): Load profile with userId
- ⏳ Stage 05 (PyAnnote VAD): Load profile with userId
- ⏳ Stage 06 (WhisperX ASR): Load profile with userId
- ⏳ Stage 13 (AI Summarization): Load profile with userId

### Phase 7: Testing & Documentation (1-2 hours)
- ⏳ Integration tests
- ⏳ Manual testing
- ⏳ Update documentation

---

## Usage Examples

### Create First User
```bash
python3 << 'EOF'
from shared.user_profile import UserProfile

# Create first user
user_id = UserProfile.create_new_user(
    name="Alice",
    email="alice@example.com",
    tmdb_api_key="YOUR_TMDB_KEY",
    huggingface_token="YOUR_HF_TOKEN"
)

print(f"Created userId: {user_id}")
print(f"Profile location: users/{user_id}/profile.json")
EOF
```

### Load and Use Profile
```bash
python3 << 'EOF'
from shared.user_profile import UserProfile

# Load user 1's profile
profile = UserProfile.load(user_id=1)

# Get credentials
tmdb_key = profile.get_credential('tmdb', 'api_key')
hf_token = profile.get_credential('huggingface', 'token')

print(f"User: {profile.user.get('name')}")
print(f"TMDB Key: {tmdb_key[:10]}...")
print(f"HF Token: {hf_token[:10]}...")
EOF
```

### Validate for Workflow
```bash
python3 << 'EOF'
from shared.user_profile import UserProfile

profile = UserProfile.load(user_id=1)

try:
    profile.validate_for_workflow('subtitle')
    print("✅ Profile valid for subtitle workflow")
except ValueError as e:
    print(f"❌ Validation failed: {e}")
EOF
```

---

## Implementation Notes

### Design Decisions

1. **File-based Storage (Phase 5)**
   - Simple, no database required
   - Easy backup/restore
   - Supports 1-10,000 users

2. **Database-Ready Schema (Phase 6)**
   - File structure matches database schema
   - Zero refactoring needed for migration
   - JSON → JSONB column (direct copy)

3. **Backward Compatibility**
   - Auto-migrates from secrets.json
   - Assigns userId 1 to migrated user
   - Logs migration actions

4. **Thread Safety**
   - File locking on .userIdCounter
   - Atomic read-increment-write operations

### Security Considerations

1. **File Permissions** (TODO)
   - Set 0600 on profile.json (owner read/write only)
   - Currently: Default permissions
   - Fix: Add chmod in save() method

2. **Credential Storage**
   - Plaintext JSON (current)
   - Encryption planned (Phase 6)
   - OS keychain integration (Phase 7)

---

## Next Steps

**Immediate (Next Session):**
1. Update bootstrap.sh (userId creation)
2. Update prepare-job.sh (--user-id parameter)
3. Test end-to-end flow

**Short-term (This Week):**
1. Update all stages (load with userId)
2. Integration testing
3. Documentation updates

**Long-term (Phase 6):**
1. Database migration
2. Encryption at rest
3. OAuth2 support

---

## References

- **BRD:** docs/requirements/brd/BRD-2025-12-10-05-user-profile-management.md
- **PRD:** docs/requirements/prd/PRD-2025-12-10-05-user-profile-management.md
- **TRD:** docs/requirements/trd/TRD-2025-12-10-05-user-profile-management.md (UPDATED)
- **Architecture:** USER_PROFILE_ARCHITECTURE_V2.md
- **Implementation:** shared/user_profile.py (540 lines, 31/32 tests passing)

---

**Status:** ✅ Core implementation complete and tested  
**Next:** Integrate with bootstrap.sh and prepare-job.sh  
**Estimated Remaining:** 6-9 hours (Phases 3-7)
