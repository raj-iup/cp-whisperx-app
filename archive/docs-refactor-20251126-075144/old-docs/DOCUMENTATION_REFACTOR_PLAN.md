# Documentation Refactor Plan

**Date:** November 26, 2025  
**Status:** PLANNED  
**Goal:** Reduce 200+ docs to 18 essential files (90% reduction)

---

## Current State

### Problems
- 200+ markdown files (massive redundancy)
- 10 files in root directory (only README.md should be there)
- Multiple "COMPLETE" and "SUMMARY" documents
- Outdated implementation histories
- Duplicate content across files
- No clear documentation structure

### Impact
- Hard to find information
- Outdated content confuses users
- Maintenance nightmare
- New developers overwhelmed

---

## Target Structure

```
cp-whisperx-app/
├── README.md                          # ✅ Project overview (refactored)
│
├── docs/
│   ├── INDEX.md                       # 📝 Documentation hub (NEW)
│   ├── QUICKSTART.md                  # 📝 Fast start guide (NEW)
│   ├── DEVELOPER_STANDARDS_COMPLIANCE.md  # ✅ Dev standards (done)
│   ├── DEVELOPER_GUIDE.md             # ✅ Dev reference
│   ├── PROCESS.md                     # ✅ Development process
│   │
│   ├── user-guide/
│   │   ├── README.md                  # User guide index
│   │   ├── bootstrap.md               # Environment setup
│   │   ├── prepare-job.md             # Job preparation
│   │   ├── workflows.md               # Workflow modes
│   │   ├── configuration.md           # Configuration guide
│   │   ├── troubleshooting.md         # Common issues
│   │   └── glossary-builder.md        # Glossary system
│   │
│   ├── technical/
│   │   ├── README.md                  # Technical index
│   │   ├── architecture.md            # System architecture
│   │   ├── pipeline.md                # Pipeline internals
│   │   ├── multi-environment.md       # Environment architecture
│   │   └── language-support.md        # Supported languages
│   │
│   ├── reference/
│   │   ├── README.md                  # Reference index
│   │   ├── changelog.md               # Version history
│   │   ├── citations.md               # Credits & sources
│   │   └── license.md                 # License
│   │
│   └── archive/                       # Historical docs (keep for reference)
│       ├── 2025-11-26-root-files/     # Archived root files
│       ├── implementation-history/    # Implementation docs
│       └── [existing archives]
```

**Total: 18 essential files**

---

## Refactor Actions

### Phase 1: Root Directory Cleanup

**Current:** 10 files  
**Target:** 1 file (README.md)  
**Action:** Move 9 files to `docs/archive/2025-11-26-root-files/`

Files to archive:
1. ALIGNMENT_BEAM_ENHANCEMENT_SUMMARY.md
2. COMPREHENSIVE_ANALYSIS_AND_FIXES.md
3. CONFIGURATION_GUIDELINES.md
4. IMPLEMENTATION_COMPLETE_NOV25.md
5. MLX_ALIGNMENT_BEAM_COMPARISON.md
6. PHASE1_COMPLETE.md
7. SUBTITLE_METADATA_PERMANENT_FIX.md
8. WHISPERX_SETUP_GUIDE.md
9. multi_env_summary.md

**Merge into:**
- README.md - Project overview (refactor completely)
- docs/user-guide/bootstrap.md - Environment setup content
- docs/user-guide/configuration.md - Configuration content
- docs/reference/changelog.md - Implementation milestones

### Phase 2: docs/ Root Consolidation

**Current:** 50+ files  
**Target:** 5 files  
**Action:** Archive implementation/history docs

Files to keep:
1. DEVELOPER_STANDARDS_COMPLIANCE.md ✅
2. DEVELOPER_GUIDE.md
3. PROCESS.md
4. INDEX.md (NEW)
5. QUICKSTART.md (NEW)

Files to archive (move to docs/archive/session-docs/):
- All BEAM_*.md files
- All CONFIG_*.md files  
- All GLOSSARY_*.md files
- All INTEGRATION_*.md files
- All PHASE_*.md files
- All SESSION*.md files
- All implementation completion docs

### Phase 3: Subdirectory Organization

#### docs/user-guide/ (Keep 7 files)
✅ README.md
✅ bootstrap.md - Consolidate environment setup
✅ prepare-job.md - Job preparation
✅ workflows.md - Workflow modes
✅ configuration.md - Merge CONFIGURATION_GUIDELINES.md here
✅ troubleshooting.md
✅ glossary-builder.md

Delete/Merge:
- apple-silicon-guide.md → Merge into bootstrap.md
- cps-guide.md → Merge into workflows.md or delete
- features/*.md → Merge into main user-guide docs

#### docs/technical/ (Keep 5 files)
✅ README.md
✅ architecture.md - System architecture
✅ pipeline.md - Pipeline internals
✅ multi-environment.md - Merge multi_env_summary.md here
✅ language-support.md - Supported languages

Archive:
- All analysis/ files
- All archive/ files
- All ASR_*, BIAS_*, CACHE_*, DEBUG_*, etc. implementation docs
- Keep them in docs/archive/technical/ for reference

#### docs/reference/ (Keep 4 files)
✅ README.md
✅ changelog.md - Consolidate all "COMPLETE" docs here
✅ citations.md
✅ license.md

### Phase 4: Create New Documentation

#### 1. README.md (Root)
**Purpose:** Project overview, quick start, key features
**Length:** ~200 lines
**Sections:**
- Project description
- Key features
- Quick start (3 commands)
- Documentation links
- License

#### 2. docs/INDEX.md
**Purpose:** Documentation hub
**Length:** ~150 lines
**Sections:**
- Getting Started
- User Guides
- Technical Documentation
- Developer Resources
- Reference

#### 3. docs/QUICKSTART.md
**Purpose:** Get running in 5 minutes
**Length:** ~100 lines
**Sections:**
- Prerequisites
- Install (bootstrap.sh)
- First job (prepare-job.sh)
- View results
- Next steps

---

## Content Consolidation

### Merge Strategy

#### Bootstrap Content
**Sources:**
- WHISPERX_SETUP_GUIDE.md
- docs/user-guide/bootstrap.md
- docs/user-guide/apple-silicon-guide.md

**Target:** docs/user-guide/bootstrap.md  
**Structure:**
1. Prerequisites
2. Installation (./bootstrap.sh)
3. Environment verification
4. Platform-specific notes (Apple Silicon, CUDA, CPU)
5. Troubleshooting

#### Configuration Content
**Sources:**
- CONFIGURATION_GUIDELINES.md
- docs/user-guide/configuration.md
- docs/quickstart/CONFIG_QUICK_REFERENCE.md

**Target:** docs/user-guide/configuration.md  
**Structure:**
1. Configuration hierarchy
2. Global config (config/.env.pipeline)
3. Job config (job.json)
4. Environment variables
5. Tuning guides (per workflow)
6. Quick reference

#### Architecture Content
**Sources:**
- multi_env_summary.md
- docs/technical/multi-environment.md
- docs/technical/architecture.md

**Target:** docs/technical/architecture.md  
**Structure:**
1. System overview
2. Multi-environment architecture
3. Pipeline stages
4. Data flow
5. Directory structure

#### Changelog Content
**Sources:**
- IMPLEMENTATION_COMPLETE_NOV25.md
- PHASE1_COMPLETE.md
- All "COMPLETE" docs

**Target:** docs/reference/changelog.md  
**Structure:**
- Version history (chronological)
- Major milestones
- Feature additions
- Bug fixes
- Breaking changes

---

## Execution Plan

### Step 1: Backup
```bash
# Create backup of current docs
tar -czf docs_backup_$(date +%Y%m%d).tar.gz *.md docs/
```

### Step 2: Create Archive Directories
```bash
mkdir -p docs/archive/2025-11-26-root-files
mkdir -p docs/archive/2025-11-26-session-docs
```

### Step 3: Move Root Files
```bash
mv ALIGNMENT_BEAM_ENHANCEMENT_SUMMARY.md docs/archive/2025-11-26-root-files/
mv COMPREHENSIVE_ANALYSIS_AND_FIXES.md docs/archive/2025-11-26-root-files/
# ... repeat for all 9 files
```

### Step 4: Archive docs/ Root Files
```bash
# Move all implementation/completion docs
mv docs/BEAM_*.md docs/archive/2025-11-26-session-docs/
mv docs/CONFIG_*.md docs/archive/2025-11-26-session-docs/
# ... repeat for all session docs
```

### Step 5: Clean Subdirectories
```bash
# Archive technical implementation docs
mv docs/technical/ASR_*.md docs/archive/technical/
mv docs/technical/BIAS_*.md docs/archive/technical/
# ... repeat for all implementation docs

# Merge and delete user-guide features
# (manual merge required)
```

### Step 6: Create New Documents
```bash
# Create from templates
# - README.md (refactor)
# - docs/INDEX.md (new)
# - docs/QUICKSTART.md (new)
```

### Step 7: Update Links
```bash
# Update all internal links in remaining docs
# Point to new structure
```

---

## Success Criteria

### Quantitative
- ✅ Reduce from 200+ files to 18 core files
- ✅ All redundant "COMPLETE" docs consolidated
- ✅ All implementation histories archived
- ✅ Single source of truth for each topic

### Qualitative
- ✅ Clear documentation hierarchy
- ✅ Easy to find information
- ✅ No duplicate content
- ✅ Consistent formatting
- ✅ Up-to-date with current codebase
- ✅ Follows DEVELOPER_STANDARDS_COMPLIANCE.md

### User Experience
- New user can get started in 5 minutes
- Developer can find technical details easily
- Clear path from beginner to advanced
- Maintenance is straightforward

---

## Timeline

**Preparation:** 1 hour
- Backup current docs
- Create archive directories
- Review content to consolidate

**Execution:** 3 hours
- Phase 1: Root cleanup (30 min)
- Phase 2: docs/ consolidation (1 hour)
- Phase 3: Subdirectory cleanup (1 hour)
- Phase 4: Create new docs (30 min)

**Validation:** 1 hour
- Verify all links work
- Check for missing content
- Test quick start guide
- Review with team

**Total:** 5 hours

---

## Rollback Plan

If issues arise:

```bash
# Restore from backup
tar -xzf docs_backup_YYYYMMDD.tar.gz

# Or restore specific sections
cp docs/archive/2025-11-26-root-files/*.md ./
cp docs/archive/2025-11-26-session-docs/*.md docs/
```

---

## Post-Refactor Maintenance

### Guidelines
1. **One topic, one file** - No duplicate docs
2. **Update in place** - Don't create new "SUMMARY" docs
3. **Archive old versions** - Don't delete, move to archive/
4. **Link, don't duplicate** - Reference other docs
5. **Keep README.md minimal** - Deep content in docs/

### Document Lifecycle
```
Create → Update → Archive → Delete (after 1 year)
   ↓        ↓         ↓
 docs/  In-place  docs/archive/
```

---

## Benefits

### For Users
- ✅ **Find info faster** - Clear structure
- ✅ **Get started quickly** - 5-minute quickstart
- ✅ **Less confusion** - No duplicate/outdated docs
- ✅ **Better organized** - Logical hierarchy

### For Developers
- ✅ **Easier maintenance** - Fewer files
- ✅ **Clear standards** - DEVELOPER_STANDARDS_COMPLIANCE.md
- ✅ **Less redundancy** - Single source of truth
- ✅ **Better onboarding** - Clear guides

### For Project
- ✅ **Professional appearance** - Clean structure
- ✅ **Easier contributions** - Clear where to add docs
- ✅ **Better version control** - Less noise in git
- ✅ **Sustainable** - Easy to maintain

---

## Next Steps

1. **Review this plan** - Validate approach
2. **Get approval** - Confirm refactor strategy
3. **Execute** - Follow execution plan
4. **Validate** - Test all documentation
5. **Announce** - Communicate new structure to team

---

**Status:** READY FOR EXECUTION  
**Estimated Time:** 5 hours  
**Risk:** Low (full backup, rollback plan)  
**Benefit:** High (90% reduction, better UX)
