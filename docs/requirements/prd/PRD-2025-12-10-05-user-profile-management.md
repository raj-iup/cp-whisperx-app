# PRD: User Profile Management System

**ID:** PRD-2025-12-10-05  
**Created:** 2025-12-10  
**Status:** Draft  
**Priority:** High  
**Target Release:** v3.2  
**Related BRD:** BRD-2025-12-10-05-user-profile-management.md

---

## Product Overview

### What We're Building

A unified User Profile Management System that assigns unique userIds to users, stores profiles in a centralized `users/` directory, and provides a foundation for future database-backed profile caching (scalable to millions of users).

### Why It Matters

**Current Pain Points:**
1. **No User Management:** config/secrets.json shared by all, no user identification
2. **Not Scalable:** No path to millions of users or SaaS platform
3. **Poor UX:** Users must manually edit secrets.json after every bootstrap
4. **No Extensibility:** Adding new online services requires ad-hoc credential handling
5. **Future Blocker:** No clear path to database-backed profile caching (Phase 6)

**Solution Impact:**
- ✅ userId-based profiles in centralized `users/` directory
- ✅ Each userId has separate profile (users/1/, users/2/, ...)
- ✅ One-time credential setup per userId (persistent across jobs)
- ✅ Standardized schema for all online services
- ✅ Foundation for database migration (file structure == database schema)
- ✅ Scalable to millions of users (Phase 6: PostgreSQL/MySQL)

---

## User Personas

### Persona 1: Alice (Content Creator)

**Profile:**
- Uses CP-WhisperX for YouTube video transcription and summarization
- Works on personal laptop (single user)
- Has TMDB, OpenAI, and YouTube API keys
- Non-technical, wants simple setup

**Goals:**
- Set API keys once, never think about them again
- Clear instructions: "Edit this file, add your key here"
- No risk of accidentally sharing keys (security)

**Pain Points (Current):**
- Confused by `config/secrets.json` location (inside project?)
- Worried about committing keys to git
- Has to re-enter keys after `bootstrap.sh` cleanup

**Success Criteria:**
- ✅ Assigned userId (e.g., userId 1) during bootstrap
- ✅ Profile in `users/1/profile.json`
- ✅ Bootstrap script prompts for keys interactively
- ✅ Keys persist across jobs (all jobs use --user-id 1)
- ✅ Clear error: "Add YouTube key to users/1/profile.json"

---

### Persona 2: Bob (SaaS Platform Operator)

**Profile:**
- Building a transcription SaaS platform
- Needs to support thousands (eventually millions) of users
- Each user has different API keys and preferences
- Technical, understands scalability

**Goals:**
- Separate profiles for each platform user (userId-based)
- Easy migration to database (PostgreSQL/MySQL)
- API to create/manage user profiles programmatically
- Backup and restore user data easily

**Pain Points (Current):**
- `config/secrets.json` not scalable (single file)
- No way to identify users (no userId system)
- Can't support multiple customers on same platform
- No path to database-backed storage

**Success Criteria:**
- ✅ Each platform user has `users/{userId}/profile.json`
- ✅ File structure matches database schema (easy migration)
- ✅ API to create users: `UserProfile.create_new_user()`
- ✅ Centralized `users/` directory (easy backup)
- ✅ Design validated for millions of users

---

### Persona 3: Carol (Enterprise Admin)

**Profile:**
- Manages CP-WhisperX deployment for 50+ internal users
- Needs centralized user management and monitoring
- Plans future cloud deployment with database backend
- Compliance requirements: SOC 2, GDPR

**Goals:**
- Centralized user data (all in `users/` directory)
- Easy backup and restore of user profiles
- Audit trail: Which userId ran which job
- Future: Migrate to database without code changes

**Pain Points (Current):**
- Credentials scattered across OS user home directories
- No central backup/restore solution
- No userId or user tracking system
- Each deployment requires separate credential management

**Success Criteria:**
- ✅ All user data in `users/` directory (centralized)
- ✅ Each user identified by userId (audit trail)
- ✅ File structure matches database schema (future-ready)
- ✅ Easy backup: `tar -czf users-backup.tar.gz users/`
- ✅ Compliance-ready: User data isolation, audit logs

---

## User Stories

### Epic 1: User Profile Setup

#### Story 1.1: First-Time User Setup
**As** Alice (new user)  
**I want** bootstrap script to create my user profile  
**So that** I don't have to manually create files

**Acceptance Criteria:**
- [ ] Bootstrap script checks for `~/.cp-whisperx/user.profile`
- [ ] If missing, offers to create: "Create user profile? (Y/n)"
- [ ] Prompts for essential credentials interactively:
  - HuggingFace token (required for ASR)
  - TMDB API key (optional, for subtitle workflow)
  - OpenAI API key (optional, for AI summarization)
- [ ] Creates profile with user input + template for other services
- [ ] Sets file permissions: 0600 (owner read/write only)
- [ ] Displays message: "Profile created at ~/.cp-whisperx/user.profile"

**Test Cases:**
```bash
# Test 1: New user, no existing profile
rm -f ~/.cp-whisperx/user.profile
./bootstrap.sh
# Expected: Prompts for credentials, creates profile

# Test 2: Existing profile
./bootstrap.sh
# Expected: Skips profile creation, displays "Profile found"

# Test 3: File permissions
ls -la ~/.cp-whisperx/user.profile
# Expected: -rw------- (0600)
```

---

#### Story 1.2: Migrate from secrets.json
**As** Bob (existing user with secrets.json)  
**I want** automatic migration to user profile  
**So that** I don't have to manually copy credentials

**Acceptance Criteria:**
- [ ] Migration script: `./tools/migrate-to-user-profile.py`
- [ ] Detects existing `config/secrets.json`
- [ ] Reads all credentials from secrets.json
- [ ] Creates `~/.cp-whisperx/user.profile` with migrated credentials
- [ ] Backs up secrets.json to `config/secrets.json.backup`
- [ ] Reports migration status: "Migrated 5 credentials"
- [ ] Validates migrated profile: "Profile valid ✓"

**Test Cases:**
```bash
# Test 1: Migrate with all credentials
cat config/secrets.json
# { "hf_token": "xxx", "tmdb_api_key": "yyy", ... }
./tools/migrate-to-user-profile.py
# Expected: Creates user.profile, backs up secrets.json

# Test 2: Migrate with partial credentials
echo '{"hf_token": "xxx"}' > config/secrets.json
./tools/migrate-to-user-profile.py
# Expected: Migrates available, templates missing

# Test 3: No secrets.json
rm config/secrets.json
./tools/migrate-to-user-profile.py
# Expected: Creates empty template profile
```

---

### Epic 2: Credential Access

#### Story 2.1: Load User Profile in Stages
**As** a developer (stage implementation)  
**I want** simple API to load user profile  
**So that** I can access credentials without file I/O boilerplate

**Acceptance Criteria:**
- [ ] Module: `shared/user_profile.py`
- [ ] API: `UserProfile.load()` - auto-detects profile location
- [ ] Fallback: If `~/.cp-whisperx/user.profile` missing, try `config/secrets.json`
- [ ] Returns: UserProfile object with credential access methods
- [ ] Error handling: Clear message if profile missing/invalid

**Usage Example:**
```python
from shared.user_profile import UserProfile

# Load profile (auto-detects location)
profile = UserProfile.load()

# Get credential
tmdb_key = profile.get_credential('tmdb', 'api_key')
if tmdb_key is None:
    logger.error("TMDB API key not configured")
    return 1

# Check if service enabled
if profile.has_service('youtube'):
    yt_key = profile.get_credential('youtube', 'api_key')
```

**Test Cases:**
```python
# Test 1: Load from user.profile
profile = UserProfile.load()
assert profile.location == '~/.cp-whisperx/user.profile'

# Test 2: Fallback to secrets.json
os.remove('~/.cp-whisperx/user.profile')
profile = UserProfile.load()
assert profile.location == 'config/secrets.json'

# Test 3: Missing credential
api_key = profile.get_credential('nonexistent', 'api_key')
assert api_key is None
```

---

#### Story 2.2: Validate Credentials for Workflow
**As** Alice (user running subtitle workflow)  
**I want** early validation of required credentials  
**So that** I don't waste time on a job that will fail later

**Acceptance Criteria:**
- [ ] Method: `profile.validate_for_workflow(workflow_name)`
- [ ] Workflows: 'transcribe', 'translate', 'subtitle'
- [ ] Required credentials per workflow:
  - **transcribe:** huggingface.token (ASR)
  - **translate:** huggingface.token (ASR + translation)
  - **subtitle:** huggingface.token + tmdb.api_key
- [ ] Raises: `ValueError` with clear message if credential missing
- [ ] Example: "Subtitle workflow requires TMDB API key. Add to ~/.cp-whisperx/user.profile"

**Test Cases:**
```python
# Test 1: Valid profile for subtitle workflow
profile.validate_for_workflow('subtitle')
# Expected: No exception

# Test 2: Missing TMDB key for subtitle workflow
profile.credentials['tmdb']['api_key'] = None
with pytest.raises(ValueError, match="TMDB API key"):
    profile.validate_for_workflow('subtitle')

# Test 3: Transcribe workflow (no TMDB required)
profile.validate_for_workflow('transcribe')
# Expected: No exception (TMDB not required)
```

---

### Epic 3: Multi-User Support

#### Story 3.1: Separate Profiles per OS User
**As** Bob (team lead on shared server)  
**I want** each OS user to have their own profile  
**So that** credentials don't conflict

**Acceptance Criteria:**
- [ ] Profile location: `~/.cp-whisperx/user.profile` (`~` expands to user home)
- [ ] User alice: Profile at `/home/alice/.cp-whisperx/user.profile`
- [ ] User bob: Profile at `/home/bob/.cp-whisperx/user.profile`
- [ ] No shared state between user profiles
- [ ] Job logs include: "Using profile: /home/alice/.cp-whisperx/user.profile"

**Test Cases:**
```bash
# Test 1: Create profile as user alice
su - alice
./bootstrap.sh
# Expected: Creates /home/alice/.cp-whisperx/user.profile

# Test 2: Create profile as user bob
su - bob
./bootstrap.sh
# Expected: Creates /home/bob/.cp-whisperx/user.profile

# Test 3: Verify separation
cat /home/alice/.cp-whisperx/user.profile
# Shows alice's credentials
cat /home/bob/.cp-whisperx/user.profile
# Shows bob's credentials (different)
```

---

#### Story 3.2: File Permissions Enforcement
**As** Carol (security admin)  
**I want** profile files to be readable only by owner  
**So that** other users cannot steal credentials

**Acceptance Criteria:**
- [ ] Profile creation sets permissions: 0600 (owner read/write only)
- [ ] Profile load validates permissions: Warns if too permissive
- [ ] Bootstrap script: `chmod 600 ~/.cp-whisperx/user.profile`
- [ ] Migration script: Sets 0600 on new profile
- [ ] Warning message: "Warning: Profile permissions too permissive (0644). Run: chmod 600 ~/.cp-whisperx/user.profile"

**Test Cases:**
```bash
# Test 1: Profile created with correct permissions
./bootstrap.sh
ls -la ~/.cp-whisperx/user.profile
# Expected: -rw------- (0600)

# Test 2: Load profile with wrong permissions
chmod 644 ~/.cp-whisperx/user.profile
python3 -c "from shared.user_profile import UserProfile; UserProfile.load()"
# Expected: Warning logged

# Test 3: Other users cannot read
su - alice
echo '{"credentials": {"tmdb": {"api_key": "secret"}}}' > ~/.cp-whisperx/user.profile
chmod 600 ~/.cp-whisperx/user.profile
su - bob
cat /home/alice/.cp-whisperx/user.profile
# Expected: Permission denied
```

---

### Epic 4: Schema Evolution

#### Story 4.1: Profile Versioning
**As** a developer (future maintainer)  
**I want** profile schema versioning  
**So that** I can migrate old profiles to new schema

**Acceptance Criteria:**
- [ ] Profile field: `"version": "1.0"`
- [ ] Load checks version field
- [ ] If version < current: Run migration
- [ ] Migration preserves user credentials
- [ ] Example migration: 1.0 → 1.1 (add `preferences.default_workflow`)

**Test Cases:**
```python
# Test 1: Load v1.0 profile (current)
profile = UserProfile.load()
assert profile.version == "1.0"

# Test 2: Load old profile (no version field)
old_profile = {"credentials": {"tmdb": {"api_key": "xxx"}}}
profile = UserProfile.from_dict(old_profile)
assert profile.version == "1.0"  # Auto-upgraded

# Test 3: Future migration (v1.1)
# When v1.1 released:
v1_profile = {"version": "1.0", "credentials": {...}}
profile = UserProfile.from_dict(v1_profile)
assert profile.version == "1.1"  # Auto-migrated
```

---

#### Story 4.2: Add New Online Service
**As** a developer (adding YouTube integration)  
**I want** to add YouTube credentials to schema  
**So that** users can store YouTube API keys

**Acceptance Criteria:**
- [ ] Schema extension: `online_services.youtube.api_key`
- [ ] Backward compatible: Old profiles still load
- [ ] Template includes new service (with empty values)
- [ ] Documentation: "Add YouTube key to user.profile"

**Schema Update:**
```json
{
  "version": "1.0",
  "credentials": { ... },
  "online_services": {
    "youtube": {
      "api_key": "",
      "enabled": false
    }
  }
}
```

**Test Cases:**
```python
# Test 1: Load old profile (no youtube field)
old_profile = {"version": "1.0", "credentials": {...}}
profile = UserProfile.from_dict(old_profile)
assert profile.get_credential('youtube', 'api_key') is None

# Test 2: Add YouTube credential
profile.set_credential('youtube', 'api_key', 'AIzaSyxxxxx')
profile.save()
# Expected: Profile updated with youtube credentials

# Test 3: Validate YouTube workflow
profile.validate_for_workflow('youtube')
# Expected: Raises if api_key missing
```

---

## Feature Requirements

### Functional Requirements

#### FR1: User Profile Schema
**Priority:** P0 (Must Have)

**Schema Definition:**
```json
{
  "version": "1.0",
  "user": {
    "name": "",
    "email": "",
    "created_at": "2025-12-10T18:00:00Z"
  },
  "credentials": {
    "huggingface": {
      "token": ""
    },
    "tmdb": {
      "api_key": ""
    },
    "pyannote": {
      "token": ""
    },
    "openai": {
      "api_key": "",
      "organization_id": ""
    },
    "anthropic": {
      "api_key": ""
    },
    "google": {
      "api_key": ""
    }
  },
  "online_services": {
    "youtube": {
      "api_key": "",
      "enabled": false
    },
    "vimeo": {
      "access_token": "",
      "enabled": false
    }
  },
  "preferences": {
    "default_workflow": "transcribe",
    "default_source_language": "en",
    "ai_provider": "openai",
    "enable_cost_tracking": true
  }
}
```

**Validation Rules:**
- `version`: Required, string, format "X.Y"
- `credentials.*.*`: Optional, string (can be empty)
- `online_services.*.enabled`: Boolean (default: false)
- `preferences.default_workflow`: Enum ['transcribe', 'translate', 'subtitle']

---

#### FR2: User Profile Module
**Priority:** P0 (Must Have)

**Module:** `shared/user_profile.py`  
**Size:** 400-500 lines

**Class: UserProfile**

**Methods:**
```python
@staticmethod
def load(path: Optional[Path] = None) -> UserProfile:
    """Load profile from path or auto-detect location."""
    
def get_credential(self, service: str, key: str) -> Optional[str]:
    """Get credential value. Returns None if not found."""
    
def set_credential(self, service: str, key: str, value: str) -> None:
    """Set credential value."""
    
def has_service(self, service: str) -> bool:
    """Check if service is configured and enabled."""
    
def validate_for_workflow(self, workflow: str) -> None:
    """Validate required credentials. Raises ValueError if missing."""
    
def save(self, path: Optional[Path] = None) -> None:
    """Save profile to disk with 0600 permissions."""
    
@staticmethod
def create_template(path: Path) -> UserProfile:
    """Create new profile from template."""
```

**Error Handling:**
- `FileNotFoundError`: Profile not found (clear message with path)
- `ValueError`: Invalid JSON, missing required fields
- `PermissionError`: Cannot read/write profile file

---

#### FR3: Migration Tool
**Priority:** P0 (Must Have)

**Script:** `tools/migrate-to-user-profile.py`  
**Size:** 150-200 lines

**Features:**
- Read existing `config/secrets.json`
- Map secrets.json keys to user profile schema
- Create `~/.cp-whisperx/user.profile`
- Backup secrets.json to `config/secrets.json.backup`
- Set file permissions (0600)
- Validate migration success
- Print summary report

**Mapping:**
```python
SECRETS_TO_PROFILE_MAP = {
    'hf_token': ('huggingface', 'token'),
    'tmdb_api_key': ('tmdb', 'api_key'),
    'pyannote_token': ('pyannote', 'token'),
    'PYANNOTE_API_TOKEN': ('pyannote', 'token'),
    'openai_api_key': ('openai', 'api_key'),
    'anthropic_api_key': ('anthropic', 'api_key'),
}
```

---

#### FR4: Bootstrap Integration
**Priority:** P0 (Must Have)

**Scripts:** `bootstrap.sh`, `bootstrap.ps1`

**Changes:**
1. Check for existing user profile
2. If missing, offer to create: "Create user profile? (Y/n)"
3. Prompt for essential credentials (HuggingFace, TMDB)
4. Auto-migrate from secrets.json if found
5. Create profile with user input
6. Set file permissions (0600)
7. Display success message with profile location

**Interactive Prompts:**
```bash
# Prompt 1: Create profile
echo "User profile not found. Create ~/.cp-whisperx/user.profile? (Y/n)"
read create_profile

# Prompt 2: HuggingFace token (required)
echo "Enter HuggingFace token (required for ASR):"
read hf_token

# Prompt 3: TMDB API key (optional)
echo "Enter TMDB API key (optional, for subtitle workflow) [skip]:"
read tmdb_key

# Prompt 4: OpenAI API key (optional)
echo "Enter OpenAI API key (optional, for AI summarization) [skip]:"
read openai_key
```

---

#### FR5: Stage Refactoring
**Priority:** P0 (Must Have)

**Stages to Update:**
- Stage 02 (TMDB) - Use `profile.get_credential('tmdb', 'api_key')`
- Stage 05 (PyAnnote VAD) - Use `profile.get_credential('pyannote', 'token')`
- Stage 06 (WhisperX ASR) - Use `profile.get_credential('huggingface', 'token')`
- Stage 13 (AI Summarization) - Use `profile.get_credential('openai', 'api_key')`

**Refactoring Pattern:**
```python
# BEFORE (direct secrets.json access)
import json
secrets_path = config_dir / "secrets.json"
with open(secrets_path) as f:
    secrets = json.load(f)
    api_key = secrets.get('tmdb_api_key')
if not api_key:
    logger.error("TMDB API key not found")
    return 1

# AFTER (user profile API)
from shared.user_profile import UserProfile
try:
    profile = UserProfile.load()
    profile.validate_for_workflow('subtitle')  # Early validation
    api_key = profile.get_credential('tmdb', 'api_key')
except ValueError as e:
    logger.error(f"Profile validation failed: {e}")
    return 1
```

---

### Non-Functional Requirements

#### NFR1: Security
**Priority:** P0 (Must Have)

- **File Permissions:** Profile file must be 0600 (owner read/write only)
- **Location:** Profile in user home directory (outside project directory)
- **Validation:** Warn if permissions too permissive
- **Secrets in Memory:** Credentials loaded into memory only when needed
- **No Logging:** Never log credential values (only presence/absence)

**Future (Phase 6):**
- Encryption at rest (AES-256)
- Integration with OS keychain (macOS Keychain, Windows Credential Manager)
- OAuth2 support (no plaintext API keys)

---

#### NFR2: Backward Compatibility
**Priority:** P0 (Must Have)

- **Fallback:** If `~/.cp-whisperx/user.profile` missing, try `config/secrets.json`
- **Migration:** Auto-detect secrets.json during bootstrap
- **No Breaking Changes:** Existing jobs must continue to work
- **Deprecation:** Log warning if using secrets.json (suggest migration)

**Deprecation Timeline:**
- v3.2: User profile introduced, secrets.json deprecated
- v3.3: Migration mandatory during bootstrap
- v3.4: secrets.json support removed

---

#### NFR3: Performance
**Priority:** P1 (Should Have)

- **Load Time:** Profile load <10ms (negligible overhead)
- **Caching:** Profile loaded once per job (not per stage)
- **File Size:** Profile file <10 KB (human-readable JSON)

---

#### NFR4: Usability
**Priority:** P0 (Must Have)

- **Clear Errors:** "Add TMDB key to ~/.cp-whisperx/user.profile"
- **Documentation:** Step-by-step setup guide
- **Template:** Profile template with comments
- **Validation:** Early validation (at job prep, not mid-pipeline)

**Example Error Message:**
```
❌ Subtitle workflow requires TMDB API key

To fix:
1. Edit: ~/.cp-whisperx/user.profile
2. Add: "credentials": { "tmdb": { "api_key": "YOUR_KEY_HERE" } }
3. Get key: https://www.themoviedb.org/settings/api

Or run migration: ./tools/migrate-to-user-profile.py
```

---

## Technical Specifications

### Architecture

**Components:**
1. **User Profile Module** (`shared/user_profile.py`)
   - Load/save profile from disk
   - Validate schema and credentials
   - Provide credential access API

2. **Migration Tool** (`tools/migrate-to-user-profile.py`)
   - One-time migration from secrets.json
   - Backup old secrets.json
   - Validate migration success

3. **Bootstrap Integration** (`bootstrap.sh`, `bootstrap.ps1`)
   - Interactive profile creation
   - Auto-migration from secrets.json
   - Set file permissions

4. **Stage Updates** (Stages 02, 05, 06, 13)
   - Replace secrets.json access with user profile API
   - Add validation at start of stage

**Data Flow:**
```
User runs bootstrap.sh
    ↓
Check for ~/.cp-whisperx/user.profile
    ↓
If missing → Prompt for credentials → Create profile
If exists → Load and validate
    ↓
User runs prepare-job.sh
    ↓
Load user profile → Validate for workflow
    ↓
User runs run-pipeline.sh
    ↓
Each stage loads profile → Get credentials → Execute
```

---

### Database Schema (Future - Phase 6)

**Table: user_profiles**
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    version VARCHAR(10) NOT NULL,
    credentials JSONB NOT NULL,
    online_services JSONB,
    preferences JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

**Migration Path:**
- v3.2: Local file storage only
- v3.3: Add database support (optional)
- v3.4: Database-backed profiles default (local fallback)
- v3.5: Cloud-hosted profiles (sync across devices)

---

## Testing Strategy

### Unit Tests

**Test Coverage:** 90%+

**Test Files:**
- `tests/unit/test_user_profile.py` (400+ lines, 30+ tests)
- `tests/unit/test_user_profile_migration.py` (200+ lines, 15+ tests)

**Test Cases:**
```python
class TestUserProfile:
    def test_load_from_user_profile(self):
        """Load profile from ~/.cp-whisperx/user.profile"""
        
    def test_load_fallback_to_secrets_json(self):
        """Fall back to config/secrets.json if user.profile missing"""
        
    def test_get_credential_existing(self):
        """Get existing credential returns value"""
        
    def test_get_credential_missing(self):
        """Get missing credential returns None"""
        
    def test_set_credential(self):
        """Set credential updates profile"""
        
    def test_validate_for_workflow_valid(self):
        """Validate workflow with all required credentials passes"""
        
    def test_validate_for_workflow_missing(self):
        """Validate workflow with missing credentials raises ValueError"""
        
    def test_file_permissions(self):
        """Profile saved with 0600 permissions"""
        
    def test_schema_validation(self):
        """Invalid profile schema raises ValueError"""
        
    def test_version_migration(self):
        """Old profile version auto-migrates to current"""
```

---

### Integration Tests

**Test Coverage:** 80%+

**Test Files:**
- `tests/integration/test_user_profile_integration.py` (300+ lines, 10+ tests)

**Test Cases:**
```python
class TestUserProfileIntegration:
    def test_stage02_tmdb_uses_profile(self):
        """Stage 02 (TMDB) loads credentials from user profile"""
        
    def test_stage13_ai_summarization_uses_profile(self):
        """Stage 13 (AI Summarization) loads OpenAI key from profile"""
        
    def test_bootstrap_creates_profile(self):
        """bootstrap.sh creates user profile interactively"""
        
    def test_migration_from_secrets_json(self):
        """migrate-to-user-profile.py migrates all credentials"""
        
    def test_multi_user_separation(self):
        """Two OS users have separate profiles"""
```

---

### Manual Testing

**Test Scenarios:**

1. **New User Setup**
   - Run bootstrap.sh as new user
   - Verify interactive profile creation
   - Check file permissions (0600)

2. **Migration**
   - Create test secrets.json
   - Run migration script
   - Verify all credentials migrated
   - Check backup created

3. **Multi-User**
   - Create 2 OS users (alice, bob)
   - Run bootstrap.sh as each user
   - Verify separate profiles
   - Run jobs as each user
   - Verify no credential conflicts

4. **Stage Integration**
   - Run subtitle workflow (requires TMDB)
   - Verify Stage 02 loads TMDB key from profile
   - Run AI summarization (requires OpenAI)
   - Verify Stage 13 loads OpenAI key from profile

---

## Success Metrics

### Adoption Metrics

- **Target:** 100% of new users create profile during bootstrap
- **Target:** 90%+ of existing users migrate within 1 week
- **Target:** 0 manual credential edits after profile setup

### Technical Metrics

- **Code Coverage:** 90%+ (unit tests)
- **Load Time:** <10ms (profile load)
- **File Size:** <10 KB (average profile)
- **Security:** 100% profiles with 0600 permissions

### User Experience Metrics

- **Setup Time:** <2 minutes (bootstrap + profile creation)
- **Error Rate:** <1% (profile validation failures)
- **Support Tickets:** 50% reduction in credential-related issues

---

## Documentation Requirements

### User Documentation

1. **User Guide: Setting Up Your User Profile**
   - Location: `docs/user-guide/user-profile-setup.md`
   - Topics:
     - What is a user profile?
     - First-time setup (bootstrap)
     - Adding credentials manually
     - Troubleshooting common issues

2. **Configuration Guide Update**
   - Location: `docs/user-guide/configuration.md`
   - Changes:
     - Deprecate secrets.json section
     - Add user profile section
     - Migration instructions

3. **Troubleshooting Guide Update**
   - Location: `docs/user-guide/troubleshooting.md`
   - Add section: "User Profile Issues"
     - Missing credentials
     - Wrong file permissions
     - Migration failures

### Developer Documentation

1. **Developer Guide: Accessing User Credentials**
   - Location: `docs/developer/user-profile-api.md`
   - Topics:
     - UserProfile API reference
     - Credential access patterns
     - Validation for workflows
     - Adding new online services

2. **DEVELOPER_STANDARDS.md Update**
   - Add § 22: User Profile Management
   - Mandatory patterns for credential access
   - Deprecation of direct secrets.json access

---

## Dependencies

### Prerequisites
- ✅ None (standalone feature)

### Related Features
- Task #19 (AI Summarization) - Uses user profile for OpenAI keys
- Task #20 (Cost Tracking) - Uses user profile for API credentials
- YouTube Integration - Will use user profile for YouTube API key
- Phase 6 (Cloud Features) - Database-backed profiles

---

## Acceptance Criteria Summary

**Must Have (P0) - All Complete for v3.2:**
- [ ] User profile schema defined and documented
- [ ] `shared/user_profile.py` module (400-500 lines)
- [ ] Migration tool: `tools/migrate-to-user-profile.py`
- [ ] Bootstrap integration (interactive profile creation)
- [ ] All stages (02, 05, 06, 13) use user profile API
- [ ] File permissions: 0600 enforced
- [ ] Fallback to secrets.json (backward compatibility)
- [ ] Unit tests: 90%+ coverage
- [ ] Integration tests: 80%+ coverage
- [ ] Documentation: User guide + developer guide

**Should Have (P1):**
- [ ] Profile validation on job preparation
- [ ] Clear error messages for missing credentials
- [ ] Multi-user testing (2+ users)
- [ ] Schema versioning (migration support)

**Nice to Have (P2) - Phase 6:**
- [ ] Encryption at rest
- [ ] Database schema ready
- [ ] OAuth2 support
- [ ] OS keychain integration

---

## Timeline

**Development Schedule:** 3 days (10-13 hours)

| Day | Tasks | Hours |
|-----|-------|-------|
| Day 1 | Schema + User Profile Module | 4-5 hours |
| Day 2 | Migration + Bootstrap Integration | 3-4 hours |
| Day 3 | Stage Refactoring + Documentation | 3-4 hours |

---

## Related Documents

- **BRD:** BRD-2025-12-10-05-user-profile-management.md
- **TRD:** TRD-2025-12-10-05-user-profile-management.md (to be created)
- **Architecture:** ARCHITECTURE.md (AD-015: User Profile Management) - to be created

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | System | Initial draft |
