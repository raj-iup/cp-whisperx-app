#!/bin/bash
# Create README.md files for archive directories
# Usage: ./tools/create-archive-readme.sh
# Generated: 2025-12-07

set -e

ROOT="/Users/rpatel/Projects/Active/cp-whisperx-app"
cd "$ROOT/archive"

echo "📝 Creating archive README files..."

# Function to create README for a directory
create_readme() {
    local dir="$1"
    local title="$2"
    local description="$3"
    
    if [ ! -d "$dir" ]; then
        return
    fi
    
    cat > "$dir/README.md" << EOF
# $title

**Archive Date:** $(date +%Y-%m-%d)  
**Category:** $title  
**Description:** $description

---

## Files in This Archive

EOF
    
    # List all markdown files (except README)
    local count=0
    for file in "$dir"/*.md; do
        if [ -f "$file" ] && [ "$(basename "$file")" != "README.md" ]; then
            echo "- [$(basename "$file")]($(basename "$file"))" >> "$dir/README.md"
            ((count++))
        fi
    done
    
    if [ $count -eq 0 ]; then
        echo "*(No files archived yet)*" >> "$dir/README.md"
    fi
    
    cat >> "$dir/README.md" << EOF

---

## About This Archive

These documents are historical records from the CP-WhisperX v3.0 development process. They have been archived to:

1. **Preserve History:** Maintain complete project history
2. **Clean Project Root:** Keep active documentation organized
3. **Maintain Context:** Provide reference for future decisions

---

## Navigation

- **Main Documentation:** See \`docs/\` directory
- **Current Status:** See \`IMPLEMENTATION_TRACKER.md\`
- **Architecture:** See \`ARCHITECTURE.md\`
- **Other Archives:** See \`archive/\` subdirectories

---

**Note:** These are historical documents and may not reflect the current state of the project.  
For up-to-date documentation, refer to the main \`docs/\` directory.
EOF
    
    echo "  ✓ Created: archive/$dir/README.md ($count files)"
}

# Create README for each category
create_readme "completion-reports" "Completion Reports" \
    "Implementation completion reports and validation summaries from various phases and tasks"

create_readme "test-reports" "Test Reports" \
    "End-to-end test reports, validation results, and test execution summaries"

create_readme "ad-documents" "Architectural Decision Documents" \
    "Implementation guides, progress reports, and summaries for architectural decisions"

create_readme "phase-reports" "Phase Reports" \
    "Session reports and implementation summaries from various development phases"

create_readme "plans" "Implementation Plans" \
    "Planning documents, roadmaps, and implementation strategies"

create_readme "fixes" "Fix Reports" \
    "Bug fix summaries, issue resolutions, and compliance improvements"

create_readme "status" "Status Reports" \
    "Quick status updates, audit summaries, and system status snapshots"

create_readme "analysis" "Analysis Documents" \
    "Code audits, documentation analysis, strategy documents, and investigation reports"

# Create master archive README
cat > README.md << 'EOF'
# CP-WhisperX Documentation Archive

**Last Updated:** 2025-12-07  
**Purpose:** Historical documentation from v3.0 development

---

## Archive Structure

This archive preserves historical documentation from the CP-WhisperX v3.0 development process. Documents are organized by category for easy navigation.

### Categories

| Category | Description | Count |
|----------|-------------|-------|
| [completion-reports/](completion-reports/) | Implementation completion reports and validation | ~27 files |
| [test-reports/](test-reports/) | Test execution reports and validation results | ~14 files |
| [ad-documents/](ad-documents/) | Architectural decision implementation docs | ~8 files |
| [phase-reports/](phase-reports/) | Development phase session reports | ~4 files |
| [plans/](plans/) | Implementation plans and roadmaps | ~9 files |
| [fixes/](fixes/) | Bug fix reports and issue resolutions | ~5 files |
| [status/](status/) | Status updates and audit summaries | ~4 files |
| [analysis/](analysis/) | Code audits and analysis documents | ~11 files |
| [sessions/](sessions/) | Historical session documents | ~16 files |
| [architecture/](architecture/) | Architecture document history | ~4 files |
| [implementation-tracker/](implementation-tracker/) | Tracker document history | ~5 files |

---

## Why Documents Were Archived

### Problem (Before)
- 90+ markdown files in project root
- Difficult navigation and discovery
- Redundant/outdated content
- No clear documentation hierarchy

### Solution (After)
- Clean project root (≤10 essential files)
- Organized docs/ structure
- Complete historical archive
- Clear navigation paths

---

## Current Documentation

For up-to-date documentation, see:

- **Project Overview:** [README.md](../README.md)
- **Architecture:** [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Implementation Status:** [IMPLEMENTATION_TRACKER.md](../IMPLEMENTATION_TRACKER.md)
- **User Guides:** [docs/user-guide/](../docs/user-guide/)
- **Developer Docs:** [docs/developer/](../docs/developer/)
- **Technical Docs:** [docs/technical/](../docs/technical/)

---

## Archive Timeline

Major milestones documented in this archive:

- **Phase 0** (2025-11): Foundation & compliance (100%)
- **Phase 1** (2025-11-12): File naming & standards (100%)
- **Phase 2** (2025-11-12): Testing infrastructure (100%)
- **Phase 3** (2025-11-12): StageIO migration (100%)
- **Phase 4** (2025-11-12): Stage integration (95%)
- **M-001** (2025-12-06): Documentation alignment audit (100%)

---

## Search Tips

### Find by Topic
```bash
# Search across all archive files
grep -r "your search term" archive/

# Search specific category
grep -r "ASR" archive/completion-reports/

# Find by date
find archive/ -name "*2025-12-06*"
```

### Find by Type
- **Completions:** `archive/completion-reports/*_COMPLETE.md`
- **Tests:** `archive/test-reports/TEST_*.md`
- **ADs:** `archive/ad-documents/AD-*.md`
- **Plans:** `archive/plans/*_PLAN.md`

---

## Document Lifecycle

```
1. Active Development
   ↓
2. Completion/Validation
   ↓
3. Archive (you are here)
   ↓
4. Git History (permanent record)
```

---

## Notes

- **Preservation:** All documents preserved, none deleted
- **Access:** Full content available in this archive
- **History:** Complete git history maintained
- **Reference:** Use for historical context and decisions

---

**Maintained by:** CP-WhisperX Team  
**Archive Policy:** Preserve all historical documents  
**Update Frequency:** As needed during major milestones
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Archive README files created!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Master: archive/README.md"
echo "  Categories:"
echo "    - archive/completion-reports/README.md"
echo "    - archive/test-reports/README.md"
echo "    - archive/ad-documents/README.md"
echo "    - archive/phase-reports/README.md"
echo "    - archive/plans/README.md"
echo "    - archive/fixes/README.md"
echo "    - archive/status/README.md"
echo "    - archive/analysis/README.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
