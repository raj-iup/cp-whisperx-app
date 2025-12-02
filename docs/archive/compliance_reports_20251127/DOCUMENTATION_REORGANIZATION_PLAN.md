# Documentation Reorganization Plan

**Date:** November 27, 2025  
**Purpose:** Consolidate and organize documentation for clarity and maintainability

---

## Current State Analysis

### Total Documents
- **docs/**: 38 files (19 root, 19 in subdirs)
- **archive/**: 347 files (historical)
- **Project root**: 1 file (README.md)

### Issues Identified
1. **Too many root-level docs** (19 files in docs/)
2. **Redundant content** (multiple implementation reports)
3. **Unclear organization** (mix of guides, reports, standards)
4. **Scattered information** (related docs not grouped)

---

## Reorganization Strategy

### Keep in docs/ Root
**Only 5 essential documents:**

1. **README.md** - Overview and quick links
2. **INDEX.md** - Complete documentation index
3. **QUICKSTART.md** - Quick start guide
4. **DEVELOPER_STANDARDS.md** - Development standards (canonical)
5. **CODEBASE_COMPLIANCE_REPORT.md** - Compliance status

### Subdirectory Structure

```
docs/
├── README.md                          # Overview
├── INDEX.md                           # Navigation
├── QUICKSTART.md                      # Quick start
├── DEVELOPER_STANDARDS.md             # Standards (canonical)
├── CODEBASE_COMPLIANCE_REPORT.md      # Compliance report
│
├── user-guide/                        # For end users
│   ├── README.md
│   ├── bootstrap.md
│   ├── configuration.md
│   ├── prepare-job.md
│   ├── workflows.md
│   ├── glossary-builder.md
│   └── troubleshooting.md
│
├── developer/                         # For developers
│   ├── README.md
│   ├── getting-started.md
│   ├── standards.md                   # Link to DEVELOPER_STANDARDS.md
│   ├── patterns.md                    # Code patterns
│   ├── testing.md                     # Testing guide
│   └── contributing.md                # Contribution guide
│
├── technical/                         # Technical specs
│   ├── README.md
│   ├── architecture.md
│   ├── pipeline.md
│   ├── multi-environment.md
│   ├── language-support.md
│   └── debug-logging.md
│
├── reference/                         # Reference material
│   ├── README.md
│   ├── changelog.md
│   ├── citations.md
│   └── license.md
│
├── implementation/                    # Implementation reports
│   ├── README.md
│   ├── priority-0-complete.md
│   ├── priority-1-complete.md
│   ├── 100-percent-complete.md
│   ├── mlx-backend.md
│   ├── standards-changelog.md
│   └── standards-quality-review.md
│
└── archive/                           # Historical docs
    ├── README.md
    ├── compliance-investigation-20251126.md
    └── developer-standards-v2-20251126.md
```

---

## Files to Move

### To implementation/
- 100_PERCENT_COMPLETE.md
- PRIORITY_0_COMPLETE.md
- PRIORITY_1_COMPLETE.md
- STANDARDS_CHANGELOG.md
- STANDARDS_QUALITY_REVIEW.md
- MLX_BACKEND_IMPLEMENTATION.md
- FUTURE_ENHANCEMENTS_IMPLEMENTATION.md

### To archive/
- ASR_COMPLIANCE_FIX.md
- BACKEND_COMPATIBILITY_FIXES.md
- CROSS_ENVIRONMENT_IMPORT_FIX.md
- MLX_DEPENDENCIES_FIX.md
- LIGHTWEIGHT_AUDIO_LOADER.md
- FUTURE_ENHANCEMENTS_ACCURACY_IMPACT.md
- DEVELOPER_STANDARDS_COMPLIANCE_v2.0_20251126.md (already there)

### To developer/
- DEVELOPER_GUIDE.md → getting-started.md
- PROCESS.md → contributing.md

### Keep Hidden
- .DOCUMENTATION_GUIDE.md (internal tool)

---

## Files to Remove/Consolidate

### Redundant Files
These contain outdated or duplicate information:

1. **ASR_COMPLIANCE_FIX.md** - Superseded by 100_PERCENT_COMPLETE.md
2. **BACKEND_COMPATIBILITY_FIXES.md** - Historical fix, now integrated
3. **CROSS_ENVIRONMENT_IMPORT_FIX.md** - Historical fix, now integrated
4. **MLX_DEPENDENCIES_FIX.md** - Historical fix, now integrated
5. **LIGHTWEIGHT_AUDIO_LOADER.md** - Technical note, archive

### Action: Move to archive/historical-fixes/

---

## New Documents to Create

### developer/patterns.md
Content: Code patterns and examples
- Configuration pattern
- Logging pattern
- StageIO pattern
- Error handling pattern
- Dual mode pattern

### developer/testing.md
Content: Testing guidelines
- Unit testing
- Integration testing
- Import tests
- Pattern tests

### implementation/README.md
Content: Index of all implementation reports
- Links to all completed priorities
- Timeline
- Summary

---

## Final Structure (Target)

```
docs/
├── README.md                          # 1. Overview
├── INDEX.md                           # 2. Navigation hub
├── QUICKSTART.md                      # 3. Quick start
├── DEVELOPER_STANDARDS.md             # 4. Standards (canonical)
├── CODEBASE_COMPLIANCE_REPORT.md      # 5. Current compliance
│
├── user-guide/ (7 files)
│   └── [No changes needed]
│
├── developer/ (6 files)
│   ├── README.md                      # NEW
│   ├── getting-started.md             # FROM DEVELOPER_GUIDE.md
│   ├── standards.md                   # Link to ../DEVELOPER_STANDARDS.md
│   ├── patterns.md                    # NEW
│   ├── testing.md                     # NEW
│   └── contributing.md                # FROM PROCESS.md
│
├── technical/ (6 files)
│   └── [No changes needed]
│
├── reference/ (4 files)
│   └── [No changes needed]
│
├── implementation/ (8 files)
│   ├── README.md                      # NEW
│   ├── priority-0-complete.md         # FROM PRIORITY_0_COMPLETE.md
│   ├── priority-1-complete.md         # FROM PRIORITY_1_COMPLETE.md
│   ├── 100-percent-complete.md        # FROM 100_PERCENT_COMPLETE.md
│   ├── mlx-backend.md                 # FROM MLX_BACKEND_IMPLEMENTATION.md
│   ├── standards-changelog.md         # FROM STANDARDS_CHANGELOG.md
│   ├── standards-quality-review.md    # FROM STANDARDS_QUALITY_REVIEW.md
│   └── future-enhancements.md         # FROM FUTURE_ENHANCEMENTS_IMPLEMENTATION.md
│
└── archive/ (9 files)
    ├── README.md                      # UPDATED
    ├── compliance-investigation-20251126.md
    ├── developer-standards-v2-20251126.md
    └── historical-fixes/              # NEW SUBDIR
        ├── asr-compliance-fix.md
        ├── backend-compatibility-fixes.md
        ├── cross-environment-import-fix.md
        ├── mlx-dependencies-fix.md
        └── lightweight-audio-loader.md
```

**Total Root Files: 5 (down from 19)** ✅
**Total Subdirectory Files: 39**
**Total Archived: ~350+**

---

## Benefits

### For Users
- ✅ Clear entry point (README + QUICKSTART)
- ✅ Easy navigation (INDEX)
- ✅ Grouped by purpose (user-guide/, technical/, etc.)
- ✅ Less clutter

### For Developers
- ✅ Clear development standards
- ✅ Code patterns documented
- ✅ Testing guidelines available
- ✅ Contribution process clear

### For Maintainers
- ✅ Organized structure
- ✅ Less redundancy
- ✅ Clear file purposes
- ✅ Easy to update

---

## Implementation Steps

1. ✅ Create DOCUMENTATION_REORGANIZATION_PLAN.md
2. Create new directories (developer/, implementation/)
3. Create new README files for each directory
4. Move files to appropriate locations
5. Rename files for consistency
6. Update internal links
7. Update INDEX.md
8. Update root README.md
9. Test all links
10. Commit changes

---

## Timeline

- Planning: 15 min (DONE)
- Execution: 30-45 min
- Testing: 15 min
- **Total: ~1 hour**

---

## Success Criteria

- [ ] Only 5 files in docs/ root
- [ ] All files in appropriate subdirectories
- [ ] No duplicate content
- [ ] All links working
- [ ] INDEX.md complete
- [ ] README.md clear and concise

