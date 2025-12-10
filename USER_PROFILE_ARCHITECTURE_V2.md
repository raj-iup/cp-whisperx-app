# User Profile Architecture Update - v2.0

**Date:** 2025-12-10  
**Status:** ✅ Requirements Updated  
**Impact:** HIGH - Complete redesign of user management system

---

## Executive Summary

**What Changed:**
- User profile system completely redesigned for scalability
- From: OS-user based (`~/.cp-whisperx/user.profile`)
- To: userId-based (`users/{userId}/profile.json`)

**Why:**
- **Scalability:** Support millions of users (future SaaS platform)
- **Database-Ready:** File structure == database schema (zero refactoring)
- **Centralized:** All user data in `users/` directory (easy backup/migration)
- **Multi-Tenant:** Foundation for multi-user applications

---

## Architecture Comparison

### OLD Architecture (v1.0) - Rejected

```
~/.cp-whisperx/user.profile         # Per OS user (alice, bob, etc.)

Limitations:
❌ Tied to OS user accounts (not scalable)
❌ No user identification system
❌ No path to database migration
❌ Limited to single machine
❌ Scattered across user home directories
```

### NEW Architecture (v2.0) - Approved

```
users/
├── 1/
│   ├── profile.json               # userId 1
│   └── cache/                     # User-specific cache
├── 2/
│   ├── profile.json               # userId 2
│   └── cache/
├── 3/
│   ├── profile.json               # userId 3
│   └── cache/
└── .userIdCounter                 # Track next available userId

Benefits:
✅ userId-based (scalable to millions)
✅ Database-ready (file structure == schema)
✅ Centralized (all in users/ directory)
✅ Multi-tenant ready
✅ Easy backup/restore
```

---

## Key Changes

### 1. User Identification System

**OLD:**
- No user identification
- One OS user = one profile
- No way to track users

**NEW:**
- Each user gets unique userId (1, 2, 3, ...)
- userId assigned during bootstrap
- .userIdCounter tracks next available userId

**Example:**
```bash
# First user
./bootstrap.sh
# Creates users/1/profile.json
# Displays: "Your userId is: 1"

# Second user
./bootstrap.sh
# Creates users/2/profile.json
# Displays: "Your userId is: 2"
```

---

### 2. Profile Location

**OLD:**
```
~/.cp-whisperx/user.profile
```

**NEW:**
```
users/{userId}/profile.json
```

**Rationale:**
- Centralized in project directory
- Database migration path clear
- Easy backup: `tar -czf users-backup.tar.gz users/`
- File structure matches database schema

---

### 3. User Profile Schema

**OLD Schema:**
```json
{
  "version": "1.0",
  "user": {...},
  "credentials": {...}
}
```

**NEW Schema:**
```json
{
  "userId": 1,                    ← NEW: User identification
  "version": "1.0",
  "user": {
    "name": "Alice",
    "email": "alice@example.com",
    "created_at": "2025-12-10T18:00:00Z"
  },
  "credentials": {...},
  "online_services": {...},
  "preferences": {...}
}
```

---

### 4. API Changes

**OLD API:**
```python
# Load profile (auto-detect location)
profile = UserProfile.load()

# Get credential
api_key = profile.get_credential('tmdb', 'api_key')
```

**NEW API:**
```python
# Bootstrap: Create new user
user_id = UserProfile.create_new_user(name="Alice", email="alice@example.com")
# Returns: 1 (next available userId)

# Stages: Load profile by userId
profile = UserProfile.load(user_id=1)

# Get credential (same as before)
api_key = profile.get_credential('tmdb', 'api_key')
```

---

### 5. Job Preparation

**OLD:**
```bash
./prepare-job.sh --media in/file.mp4 --workflow transcribe
```

**NEW:**
```bash
./prepare-job.sh --user-id 1 --media in/file.mp4 --workflow transcribe
                 ^^^^^^^^^^^
                 Required: Specify which user
```

**Why:**
- Multiple users can use same system
- Job logs show which userId ran the job
- Cost tracking per userId
- Audit trail (userId → job → API costs)

---

### 6. Migration from secrets.json

**OLD:**
```bash
./tools/migrate-to-user-profile.py
# Migrates to: ~/.cp-whisperx/user.profile
```

**NEW:**
```bash
./tools/migrate-to-user-profile.py
# Migrates to: users/1/profile.json
# First migrated user always gets userId 1
```

---

## Database Migration Path (Phase 6)

### Current: File-Based Storage

```
users/
├── 1/profile.json
├── 2/profile.json
└── 3/profile.json
```

### Future: Database-Backed Storage

```sql
CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY,         -- Same as file: userId
    version VARCHAR(10) NOT NULL,        -- Same as file: version
    name VARCHAR(255),                   -- From user.name
    email VARCHAR(255),                  -- From user.email
    profile_data JSONB NOT NULL,         -- Entire JSON (credentials, preferences)
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_user_profiles_email ON user_profiles(email);
```

### Migration Process (Phase 6)

```python
# Step 1: Read file-based profile
with open('users/1/profile.json') as f:
    profile = json.load(f)

# Step 2: Insert into database (EXACT same structure)
db.execute("""
    INSERT INTO user_profiles (user_id, profile_data, created_at)
    VALUES (%s, %s, %s)
""", (profile['userId'], json.dumps(profile), profile['user']['created_at']))

# That's it! Zero refactoring needed.
```

**Key Benefit:** File structure == Database schema → ZERO code changes

---

## Scalability Analysis

### File-Based (Current - v3.2)

**Capacity:**
- 10,000 users = 10,000 files in users/ directory
- Linux file system limit: ~2 million files per directory
- **Max users (file-based):** ~1-2 million

**Performance:**
- User 1: Read `users/1/profile.json` (fast)
- User 1000: Read `users/1000/profile.json` (fast)
- User 1,000,000: Read `users/1000000/profile.json` (still fast)

**Limits:**
- Backup time increases (1M files)
- Directory listing slow (ls users/)
- No transactions (concurrent writes risky)

### Database-Backed (Future - Phase 6)

**Capacity:**
- PostgreSQL: Billions of rows
- MySQL: Billions of rows
- **Max users (database):** Unlimited (practically)

**Performance:**
- Indexed lookups: O(log n) - very fast
- Concurrent access: Built-in
- Transactions: ACID guarantees
- Caching: Redis/Memcached integration

**When to Migrate:**
- File-based: 1-10,000 users (Phase 5)
- Hybrid: 10,000-100,000 users (Phase 6 transition)
- Database: 100,000+ users (Phase 6 full migration)

---

## Use Cases

### Use Case 1: Personal Use (1 user)

```bash
# Bootstrap assigns userId 1
./bootstrap.sh
# Your userId is: 1

# Run jobs with userId 1
./prepare-job.sh --user-id 1 --media in/video.mp4
```

**Structure:**
```
users/
└── 1/
    └── profile.json
```

---

### Use Case 2: Small Team (5-10 users)

```bash
# Team member 1
./bootstrap.sh  # userId 1

# Team member 2
./bootstrap.sh  # userId 2

# Team member 3
./bootstrap.sh  # userId 3
```

**Structure:**
```
users/
├── 1/profile.json  (Alice - TMDB key A)
├── 2/profile.json  (Bob - TMDB key B)
└── 3/profile.json  (Carol - TMDB key C)
```

**Benefits:**
- Separate credentials per user
- Cost tracking per userId
- No credential conflicts

---

### Use Case 3: SaaS Platform (1,000s of users)

```python
# API endpoint: Create user
@app.post("/api/users/create")
def create_user(name: str, email: str):
    user_id = UserProfile.create_new_user(name=name, email=email)
    return {"userId": user_id}

# API endpoint: Submit job
@app.post("/api/jobs/submit")
def submit_job(user_id: int, media_url: str):
    # Validate userId exists
    profile = UserProfile.load(user_id=user_id)
    
    # Prepare job with user's credentials
    job_id = prepare_job(user_id=user_id, media=media_url)
    return {"jobId": job_id}
```

**Structure:**
```
users/
├── 1/profile.json  (Customer 1)
├── 2/profile.json  (Customer 2)
├── ...
└── 9999/profile.json  (Customer 9999)
```

**Benefits:**
- Multi-tenant architecture
- Each customer isolated
- Easy to add new customers
- Billing per userId

---

### Use Case 4: Enterprise (Phase 6 - Database)

```sql
-- Create user (via API)
INSERT INTO user_profiles (user_id, profile_data)
VALUES (10001, '{"userId": 10001, "credentials": {...}}');

-- Load user profile
SELECT profile_data FROM user_profiles WHERE user_id = 10001;

-- Track usage
SELECT user_id, COUNT(*) as job_count
FROM jobs
GROUP BY user_id
ORDER BY job_count DESC;
```

**Benefits:**
- Millions of users supported
- Fast lookups (indexed)
- Analytics queries
- Backup/restore via SQL dumps

---

## Migration Timeline

### Phase 5 (File-Based) - v3.2 to v3.4

**Duration:** 2-3 months  
**User Capacity:** 1-10,000 users

**Features:**
- ✅ userId assignment system
- ✅ File-based storage (users/ directory)
- ✅ Bootstrap integration
- ✅ Migration from secrets.json
- ✅ All stages use userId-based API

---

### Phase 6 (Database-Backed) - v3.5 to v4.0

**Duration:** 3-6 months  
**User Capacity:** 10,000+ users (unlimited)

**Features:**
- ✅ PostgreSQL/MySQL support
- ✅ Automatic migration (file → database)
- ✅ Hybrid mode (file + database)
- ✅ API authentication (OAuth2)
- ✅ User management dashboard
- ✅ Analytics and reporting

---

## Updated BRD-PRD-TRD Documents

### BRD-2025-12-10-05 (Updated)
- ✅ New stakeholder: SaaS Platform Operators
- ✅ Success criteria: userId system, database-ready
- ✅ Updated implementation approach (userId assignment)
- ✅ Scalability section (millions of users)

### PRD-2025-12-10-05 (Updated)
- ✅ New persona: Bob (SaaS Platform Operator)
- ✅ Updated user stories (userId-based)
- ✅ API changes (create_new_user, load with userId)
- ✅ prepare-job.sh: --user-id parameter

### TRD-2025-12-10-05 (To Be Updated)
- ⏳ Component specs (UserProfile class)
- ⏳ userId assignment algorithm
- ⏳ .userIdCounter file format
- ⏳ Database schema (Phase 6)
- ⏳ Migration scripts

---

## Action Items

### Immediate (This Week)
1. ✅ Update BRD with userId system
2. ✅ Update PRD with new personas/stories
3. ⏳ Update TRD with technical specs
4. ⏳ Review and approve architecture change

### Short-term (Next Week)
1. ⏳ Implement userId assignment system
2. ⏳ Create users/ directory structure
3. ⏳ Update bootstrap.sh (assign userId)
4. ⏳ Update prepare-job.sh (--user-id parameter)

### Long-term (Phase 6)
1. ⏳ Database schema design
2. ⏳ File → Database migration tool
3. ⏳ Hybrid mode (file + database)
4. ⏳ API authentication

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| File system limits (>1M users) | LOW | HIGH | Migrate to database (Phase 6) |
| Concurrent userId assignment | MEDIUM | MEDIUM | File locking on .userIdCounter |
| Directory listing slow (>100K users) | MEDIUM | LOW | Hierarchical structure (users/1/00/01/) |
| Backup time increases | HIGH | MEDIUM | Incremental backups, database replication |

---

## Approval

**Architecture Change:** userId-based profiles in `users/` directory  
**Status:** ✅ Approved  
**Next:** Update TRD and begin implementation

---

**Document Version:** 2.0  
**Last Updated:** 2025-12-10  
**Author:** System Architecture Team
