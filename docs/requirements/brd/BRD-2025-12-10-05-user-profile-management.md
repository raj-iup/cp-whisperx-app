# BRD: User Profile Management System

**ID:** BRD-2025-12-10-05  
**Created:** 2025-12-10  
**Status:** Draft  
**Priority:** High  
**Target Release:** v3.2

---

## Business Objective

### Why This is Needed

**Problem Statement:**
User-specific credentials and settings (API keys, preferences, online service tokens) are currently scattered across multiple locations (`config/secrets.json`, environment variables, job-specific configs). This creates security risks, poor user experience, and makes future database-backed profile caching impossible.

**Background:**
- **Current State:** secrets.json contains sensitive credentials (Hugging Face tokens, TMDB API keys, PyAnnote tokens, Anthropic/OpenAI keys)
- **Issue #1:** secrets.json is user-specific but stored in project config directory (shared location)
- **Issue #2:** No clear separation between system config and user credentials
- **Issue #3:** Adding new online services (YouTube, Vimeo, cloud storage) requires ad-hoc credential handling
- **Issue #4:** Future database-backed profile caching requires consistent user profile structure
- **Issue #5:** Multiple users on same system cannot maintain separate profiles

**Current Workarounds:**
- Users manually edit `config/secrets.json` after bootstrap
- Credentials mixed with system configuration
- No versioning or migration path for user profiles
- No validation of credential format/completeness
- No encryption at rest (plaintext secrets)

**Proposed Solution:**
Create a unified User Profile Management System that:
1. Separates user credentials from system configuration
2. Provides a dedicated `users/{userId}/profile.json` location (project directory, database-ready)
3. Assigns unique userId to each user (starting from 1, 2, 3...)
4. Establishes a clear schema for credentials, preferences, and online service tokens
5. Enables future database-backed profile caching (millions of users)
6. Supports multiple users through userId-based directories
7. Provides credential validation and secure storage

**Strategic Benefits:**
- **Scalability:** Designed for millions of users (future database migration)
- **Multi-user:** Each userId has separate profile directory
- **Database-Ready:** File structure mirrors future database schema
- **Centralized:** All user data in `users/` directory (easy backup/migration)
- **Extensibility:** Easy to add new online services (YouTube, Vimeo, Dropbox, etc.)
- **User Experience:** One-time credential setup per userId, reused across all jobs

---

## Stakeholder Requirements

### Primary Stakeholders

**1. End Users (Content Creators, Researchers, Students)**
- **Need:** Secure, persistent storage of API credentials
- **Expected Outcome:** Set credentials once, never worry about them again
- **Success Metric:** 100% credential persistence across jobs and system restarts

**2. Multi-User System Administrators**
- **Need:** Separate profiles for different users (userId-based)
- **Expected Outcome:** User 1 and User 2 can use same system with different TMDB/OpenAI keys
- **Success Metric:** Zero credential conflicts between userIds

**3. SaaS Platform Operators**
- **Need:** Scalable user management system (millions of users in future)
- **Expected Outcome:** Easy migration from file-based to database-backed profiles
- **Success Metric:** File structure matches database schema (zero refactoring needed)

**4. Future Cloud Users (Phase 6+)**
- **Need:** Profile portability (sync across devices via database)
- **Expected Outcome:** Same profile on laptop, desktop, cloud instance
- **Success Metric:** Database-backed caching architecture ready

### Secondary Stakeholders

**5. Developers**
- **Impact:** New shared/user_profile.py module, refactor credential loading
- **Need:** Clean API for credential access, backward compatibility during migration
- **Success Metric:** <600 LOC, all stages migrated in 1 sprint

**6. DevOps Engineers**
- **Impact:** Bootstrap script changes, new file locations
- **Need:** Automatic migration from secrets.json to user.profile
- **Success Metric:** Zero manual user intervention during upgrade

---

## Success Criteria

### Quantifiable Metrics

- [x] **Migration:** 100% of existing credentials migrated from secrets.json to users/{userId}/profile.json
- [x] **Adoption:** 100% of stages use user_profile.py API (no direct secrets.json access)
- [x] **User Management:** userId assignment system working (auto-increment from 1)
- [x] **Multi-user:** 2+ userIds on same system with different profiles (tested)
- [x] **Backward Compat:** 0 job failures during migration (graceful fallback)
- [x] **Future-ready:** File structure matches database schema (validated)
- [x] **Scalability:** Design supports millions of users (architecture validated)

### Qualitative Success Indicators

- ✅ User credentials clearly separated from system configuration
- ✅ Bootstrap script automates user profile creation
- ✅ Clear documentation: "Add your TMDB key to ~/.cp-whisperx/user.profile"
- ✅ Profile validation on job preparation (missing credentials detected early)
- ✅ Extensible schema (easy to add YouTube, Vimeo, Dropbox tokens)
- ✅ Developer-friendly API (simple `get_credential('tmdb_api_key')`)

---

## Business Value

### Benefits

**1. Centralized User Management**
- **Before:** No central user directory, credentials scattered
- **After:** All users in `users/` directory, userId-based organization
- **Value:** Easy backup, migration, and future database transition

**2. Scalability (Design for Millions)**
- **Before:** OS-user based (limited to single machine)
- **After:** userId-based (scalable to millions via database)
- **Value:** Foundation for SaaS platform, multi-tenant architecture

**3. User Experience**
- **Before:** Edit config/secrets.json after every bootstrap
- **After:** userId assigned once, credentials persistent
- **Value:** 90% reduction in credential management friction

**4. Database Migration Path (Future)**
- **Before:** No clear path to cloud-hosted profiles
- **After:** File structure == database schema (zero refactoring)
- **Value:** Enables Phase 6 cloud features (profile sync, API access)

**5. Extensibility**
- **Before:** Ad-hoc credential handling for each new service
- **After:** Standardized schema: `online_services.youtube.api_key`
- **Value:** 50% faster integration of new online services

### Cost Considerations

**Implementation Cost:**
- Development: 6-8 hours (user_profile.py module + migration script)
- Testing: 2-3 hours (multi-user testing, backward compatibility)
- Documentation: 2 hours (user guide, developer guide updates)
- **Total:** 10-13 hours

**Operational Cost:**
- Bootstrap time: +30 seconds (one-time profile setup)
- Maintenance: Minimal (profile schema versioning)

**ROI:**
- Security risk reduction: High value
- Multi-user support: High value for teams
- Future database-backed profiles: Foundation for Phase 6 (estimated 20 hour savings)
- **Payback:** Immediate for multi-user scenarios

---

## Constraints & Dependencies

### Technical Constraints

1. **Backward Compatibility:** Must support existing jobs that expect secrets.json
2. **File Permissions:** User profile must be readable only by owner (0600)
3. **Schema Evolution:** Profile schema must support versioning/migration
4. **Validation:** Missing credentials must fail early (at job prep, not mid-pipeline)

### Dependencies

**Prerequisite:**
- ✅ None (standalone feature)

**Related Features:**
- Task #19 (AI Summarization) - Uses user profile for OpenAI/Gemini keys
- Task #20 (Cost Tracking) - Uses user profile for API credentials
- YouTube Integration - Will use user profile for YouTube API key

**External Dependencies:**
- None (pure Python, standard library only)

---

## Assumptions & Risks

### Assumptions

1. ✅ Users have write access to their home directory (`~/`)
2. ✅ OS supports `~` expansion (Linux, macOS, Windows with Python pathlib)
3. ✅ User profile is JSON format (human-editable)
4. ✅ Credentials are stored in plaintext initially (encryption in Phase 6)

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users don't migrate from secrets.json | MEDIUM | LOW | Auto-migration during bootstrap |
| Profile file permissions too permissive | LOW | HIGH | Set 0600 permissions on creation |
| Schema evolution breaks old profiles | LOW | MEDIUM | Version field + migration scripts |
| Users edit profile incorrectly | MEDIUM | MEDIUM | Validation on job prep, clear error messages |

---

## Out of Scope (Future Phases)

**Not Included in v3.2:**
- ❌ Encryption at rest (plaintext credentials for now)
- ❌ Database-backed profile storage (local files only)
- ❌ Profile synchronization across devices
- ❌ Team/organization-level profiles
- ❌ OAuth2 flows (direct API key entry only)
- ❌ Credential expiration/rotation tracking
- ❌ Multi-factor authentication
- ❌ Audit logging for credential access

**Future Roadmap:**
- **Phase 6 (Cloud Features):** Database-backed profiles, sync across devices
- **Phase 7 (Enterprise):** Team profiles, SSO, audit logging
- **Phase 8 (Security):** Encryption at rest, credential rotation

---

## Implementation Approach

### Phase 1: User Profile Schema Definition (1 hour)

**Deliverable:** User profile JSON schema + userId management

```json
{
  "userId": 1,
  "version": "1.0",
  "user": {
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2025-12-10T18:00:00Z"
  },
  "credentials": {
    "huggingface": {
      "token": "hf_xxxxx"
    },
    "tmdb": {
      "api_key": "xxxxx"
    },
    "pyannote": {
      "token": "sk_xxxxx"
    },
    "openai": {
      "api_key": "sk-xxxxx",
      "organization_id": "org-xxxxx"
    },
    "anthropic": {
      "api_key": "sk-ant-xxxxx"
    },
    "google": {
      "api_key": "AIzaSyxxxxx"
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

**Directory Structure:**
```
users/
├── 1/
│   ├── profile.json
│   └── cache/          # User-specific cache (future)
├── 2/
│   ├── profile.json
│   └── cache/
└── .userIdCounter     # Track next available userId
```

### Phase 2: User Profile Module (3-4 hours)

**Deliverable:** `shared/user_profile.py` (400-500 lines)

**Features:**
- Load profile from `users/{userId}/profile.json`
- Fallback to `config/secrets.json` (backward compatibility)
- Get credential by key: `get_credential('tmdb_api_key')`
- Validate required credentials for workflow
- Create default profile template
- userId assignment and management
- Profile versioning and migration

**API:**
```python
from shared.user_profile import UserProfile

# Create new user (bootstrap)
user_id = UserProfile.create_new_user(name="John", email="john@example.com")
# Returns: 1 (next available userId)

# Load profile by userId
profile = UserProfile.load(user_id=1)

# Get credential (returns None if not found)
tmdb_key = profile.get_credential('tmdb', 'api_key')

# Validate required credentials for workflow
profile.validate_for_workflow('subtitle')  # Raises if missing

# Check if service is configured
if profile.has_service('youtube'):
    yt_key = profile.get_credential('youtube', 'api_key')
```

### Phase 3: Migration Script (1-2 hours)

**Deliverable:** `tools/migrate-to-user-profile.py`

**Features:**
- Read existing `config/secrets.json`
- Create `users/1/profile.json` (first user gets userId 1)
- Backup old secrets.json to `config/secrets.json.backup`
- Validate migration success
- Report migration status

**Usage:**
```bash
./tools/migrate-to-user-profile.py
# Migrates credentials from secrets.json to users/1/profile.json
# Creates backup of old secrets.json
# Assigns userId 1 to migrated user
```

### Phase 4: Bootstrap Integration (1 hour)

**Deliverable:** Update `bootstrap.sh` and `bootstrap.ps1`

**Changes:**
- Check for existing users in `users/` directory
- Offer to create new user profile
- Prompt for essential credentials (HuggingFace, TMDB)
- Auto-migrate from secrets.json if found (assigns userId 1)
- Create `users/{userId}/` directory structure
- Display assigned userId

### Phase 5: Stage Refactoring (2-3 hours)

**Deliverable:** Update all stages to use user_profile.py

**Stages to Update:**
- Stage 02 (TMDB) - TMDB API key
- Stage 06 (WhisperX ASR) - HuggingFace token
- Stage 05 (PyAnnote VAD) - PyAnnote token
- Stage 13 (AI Summarization) - OpenAI/Anthropic keys
- Future YouTube stage - YouTube API key

**Pattern:**
```python
# OLD (direct secrets.json access)
import json
with open('config/secrets.json') as f:
    secrets = json.load(f)
    api_key = secrets.get('tmdb_api_key')

# NEW (user profile API)
from shared.user_profile import UserProfile
profile = UserProfile.load()
api_key = profile.get_credential('tmdb', 'api_key')
```

### Phase 6: Documentation (2 hours)

**Updates:**
- User guide: "Setting up your user profile"
- Developer guide: "Accessing user credentials"
- Configuration guide: Update secrets.json → user.profile
- Troubleshooting: Common profile issues

---

## Acceptance Criteria

**Must Have (P0):**
- [ ] User profile schema defined and documented (with userId field)
- [ ] `shared/user_profile.py` module implemented
- [ ] Profile location: `users/{userId}/profile.json`
- [ ] userId assignment system (auto-increment from 1)
- [ ] Fallback to `config/secrets.json` (backward compatibility)
- [ ] Migration script: `tools/migrate-to-user-profile.py` (creates userId 1)
- [ ] Bootstrap integration: Auto-create new userId
- [ ] All stages use user_profile.py API with userId parameter
- [ ] User guide: Profile setup instructions
- [ ] Developer guide: Credential access patterns
- [ ] prepare-job.sh: `--user-id {userId}` parameter

**Should Have (P1):**
- [ ] Profile validation on job preparation
- [ ] Clear error messages for missing credentials
- [ ] Profile template with comments
- [ ] Multi-user testing (2+ userIds on same system)
- [ ] Schema versioning (future migration support)
- [ ] userId counter management (`.userIdCounter` file)

**Nice to Have (P2):**
- [ ] Profile encryption (Phase 6)
- [ ] Database schema for future persistence
- [ ] OAuth2 support (Phase 6)
- [ ] Credential expiration tracking (Phase 7)

---

## Related Documents

**Requirements:**
- PRD-2025-12-10-05-user-profile-management.md (to be created)
- TRD-2025-12-10-05-user-profile-management.md (to be created)

**Dependencies:**
- BRD-2025-12-10-03-ai-summarization.md (uses user profile)
- BRD-2025-12-10-02-online-media-integration.md (uses user profile)
- BRD-2025-12-10-04-cost-tracking.md (uses user profile)

**Architecture:**
- ARCHITECTURE.md (AD-015: User Profile Management) - to be created

---

## Timeline

**Development Schedule:**

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Schema Definition | 1 hour | Day 1 | Day 1 |
| User Profile Module | 3-4 hours | Day 1 | Day 2 |
| Migration Script | 1-2 hours | Day 2 | Day 2 |
| Bootstrap Integration | 1 hour | Day 2 | Day 2 |
| Stage Refactoring | 2-3 hours | Day 3 | Day 3 |
| Documentation | 2 hours | Day 3 | Day 3 |
| **Total** | **10-13 hours** | **Day 1** | **Day 3** |

**Milestones:**
- Day 1 EOD: User profile module working
- Day 2 EOD: Migration complete, bootstrap updated
- Day 3 EOD: All stages migrated, documentation complete

---

## Approval & Sign-off

**Business Owner:** Product Manager  
**Technical Owner:** Lead Developer  
**Security Review:** Required (credential storage)  
**Status:** Draft (awaiting review)

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | System | Initial draft |

