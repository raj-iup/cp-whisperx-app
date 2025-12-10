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
2. Provides a dedicated `~/.cp-whisperx/user.profile` location (user home directory)
3. Establishes a clear schema for credentials, preferences, and online service tokens
4. Enables future database-backed profile caching
5. Supports multiple users on the same system
6. Provides credential validation and secure storage

**Strategic Benefits:**
- **Security:** User credentials isolated from project directory
- **Multi-user:** Each OS user has their own profile
- **Scalability:** Foundation for cloud-hosted profile storage
- **Extensibility:** Easy to add new online services (YouTube, Vimeo, Dropbox, etc.)
- **User Experience:** One-time credential setup, reused across all jobs

---

## Stakeholder Requirements

### Primary Stakeholders

**1. End Users (Content Creators, Researchers, Students)**
- **Need:** Secure, persistent storage of API credentials
- **Expected Outcome:** Set credentials once, never worry about them again
- **Success Metric:** 100% credential persistence across jobs and system restarts

**2. Multi-User System Administrators**
- **Need:** Separate profiles for different OS users
- **Expected Outcome:** Alice and Bob can use same system with different TMDB/OpenAI keys
- **Success Metric:** Zero credential conflicts between users

**3. Security-Conscious Organizations**
- **Need:** Credentials not stored in project directory (especially git repos)
- **Expected Outcome:** Credentials in user home directory only
- **Success Metric:** Zero credential leaks via version control

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

- [x] **Migration:** 100% of existing credentials migrated from secrets.json to user.profile
- [x] **Adoption:** 100% of stages use user_profile.py API (no direct secrets.json access)
- [x] **Security:** 0 credentials stored in project directory after migration
- [x] **Multi-user:** 2+ users on same system with different profiles (tested)
- [x] **Backward Compat:** 0 job failures during migration (graceful fallback)
- [x] **Future-ready:** User profile schema supports database persistence (validated)

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

**1. Security**
- **Before:** Credentials in project directory (risk of accidental commit)
- **After:** Credentials in user home directory (outside git repo)
- **Value:** Eliminates #1 security vulnerability

**2. Multi-User Support**
- **Before:** One secrets.json shared by all OS users
- **After:** Each user has ~/.cp-whisperx/user.profile
- **Value:** Enables shared workstations, development servers

**3. User Experience**
- **Before:** Edit config/secrets.json after every bootstrap
- **After:** Set credentials once in user.profile, forget about them
- **Value:** 90% reduction in credential management friction

**4. Scalability (Future)**
- **Before:** No path to cloud-hosted profiles
- **After:** User profile schema ready for database persistence
- **Value:** Enables Phase 6 cloud features (profile sync, team sharing)

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

**Deliverable:** User profile JSON schema

```json
{
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

### Phase 2: User Profile Module (3-4 hours)

**Deliverable:** `shared/user_profile.py` (400-500 lines)

**Features:**
- Load profile from `~/.cp-whisperx/user.profile`
- Fallback to `config/secrets.json` (backward compatibility)
- Get credential by key: `get_credential('tmdb_api_key')`
- Validate required credentials for workflow
- Create default profile template
- Set file permissions (0600)
- Profile versioning and migration

**API:**
```python
from shared.user_profile import UserProfile

# Load profile (auto-detects location)
profile = UserProfile.load()

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
- Create `~/.cp-whisperx/user.profile` with migrated credentials
- Backup old secrets.json to `config/secrets.json.backup`
- Validate migration success
- Report migration status

**Usage:**
```bash
./tools/migrate-to-user-profile.py
# Migrates credentials from secrets.json to user.profile
# Creates backup of old secrets.json
# Sets correct file permissions (0600)
```

### Phase 4: Bootstrap Integration (1 hour)

**Deliverable:** Update `bootstrap.sh` and `bootstrap.ps1`

**Changes:**
- Check for existing user profile
- Offer to create profile during bootstrap
- Prompt for essential credentials (HuggingFace, TMDB)
- Auto-migrate from secrets.json if found
- Set file permissions

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
- [ ] User profile schema defined and documented
- [ ] `shared/user_profile.py` module implemented
- [ ] Profile location: `~/.cp-whisperx/user.profile`
- [ ] Fallback to `config/secrets.json` (backward compatibility)
- [ ] File permissions: 0600 (owner read/write only)
- [ ] Migration script: `tools/migrate-to-user-profile.py`
- [ ] Bootstrap integration: Auto-create profile
- [ ] All stages use user_profile.py API
- [ ] User guide: Profile setup instructions
- [ ] Developer guide: Credential access patterns

**Should Have (P1):**
- [ ] Profile validation on job preparation
- [ ] Clear error messages for missing credentials
- [ ] Profile template with comments
- [ ] Multi-user testing (2+ users on same system)
- [ ] Schema versioning (future migration support)

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

