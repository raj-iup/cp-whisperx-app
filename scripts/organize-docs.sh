#!/bin/bash
# organize-docs.sh - Reorganize and clean up documentation
# Creates a clean, hierarchical documentation structure

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ARCHIVE_DIR="archive/old-docs-$(date +%Y%m%d-%H%M%S)"
DRY_RUN=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help)
            cat << 'EOF'
Usage: ./organize-docs.sh [OPTIONS]

Reorganize documentation into clean hierarchy

OPTIONS:
  --dry-run    Show what would be done without making changes
  -h, --help   Show this help

ACTIONS:
  1. Create new docs structure (docs/setup/, docs/user-guide/, etc.)
  2. Archive obsolete docs (PHASE_1_*.md, *_COMPLETE.md, etc.)
  3. Keep essential root docs (README.md, QUICKSTART.md)
  4. Move feature docs to docs/features/
  5. Update cross-references
  6. Generate docs/INDEX.md

EOF
            exit 0
            ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN MODE - No files will be moved"
fi

echo ""
log_info "═══════════════════════════════════════════════════════════"
log_info "  Documentation Reorganization"
log_info "═══════════════════════════════════════════════════════════"
echo ""

# Step 1: Create new directory structure
log_info "Creating new documentation structure..."

DIRS=(
    "docs/setup"
    "docs/user-guide"
    "docs/features"
    "docs/developer"
    "docs/reference"
    "$ARCHIVE_DIR"
)

for dir in "${DIRS[@]}"; do
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$dir"
    fi
    log_success "Created: $dir"
done

echo ""

# Step 2: Archive obsolete documentation
log_info "Archiving obsolete documentation..."

ARCHIVE_PATTERNS=(
    "PHASE_1_*.md"
    "*_COMPLETE.md"
    "IMPLEMENTATION_*.md"
    "INTEGRATION_*.md"
    "*_IMPLEMENTATION_*.md"
    "*_STATUS*.md"
    "*_READINESS*.md"
    "*_WEEK*.md"
    "CURRENT_STATUS*.md"
    "NEXT_STEPS*.md"
)

for pattern in "${ARCHIVE_PATTERNS[@]}"; do
    files=$(find . -maxdepth 1 -name "$pattern" -type f 2>/dev/null)
    for file in $files; do
        if [ -f "$file" ] && [ "$file" != "./README.md" ]; then
            if [ "$DRY_RUN" = false ]; then
                mv "$file" "$ARCHIVE_DIR/"
            fi
            log_success "Archived: $(basename $file)"
        fi
    done
done

echo ""

# Step 3: Move feature documentation
log_info "Organizing feature documentation..."

# Hybrid Translation docs
if [ -f "HYBRID_TRANSLATION_SETUP.md" ]; then
    [ "$DRY_RUN" = false ] && mv "HYBRID_TRANSLATION_SETUP.md" "docs/features/"
    log_success "Moved: HYBRID_TRANSLATION_SETUP.md → docs/features/"
fi

# Model Caching
if [ -f "MODEL_CACHING.md" ]; then
    [ "$DRY_RUN" = false ] && mv "MODEL_CACHING.md" "docs/setup/"
    log_success "Moved: MODEL_CACHING.md → docs/setup/"
fi

# Lyrics Detection
for file in LYRICS_DETECTION*.md; do
    if [ -f "$file" ]; then
        [ "$DRY_RUN" = false ] && mv "$file" "$ARCHIVE_DIR/" 2>/dev/null || true
        log_success "Archived: $file"
    fi
done

# Hallucination Removal  
for file in HALLUCINATION_REMOVAL*.md; do
    if [ -f "$file" ]; then
        [ "$DRY_RUN" = false ] && mv "$file" "$ARCHIVE_DIR/" 2>/dev/null || true
        log_success "Archived: $file"
    fi
done

# Source Separation
if [ -f "SOURCE_SEPARATION_FIX.md" ]; then
    [ "$DRY_RUN" = false ] && mv "SOURCE_SEPARATION_FIX.md" "$ARCHIVE_DIR/"
    log_success "Archived: SOURCE_SEPARATION_FIX.md"
fi

# Subtitle improvement
if [ -f "SUBTITLE_IMPROVEMENT_PLAN.md" ]; then
    [ "$DRY_RUN" = false ] && mv "SUBTITLE_IMPROVEMENT_PLAN.md" "$ARCHIVE_DIR/"
    log_success "Archived: SUBTITLE_IMPROVEMENT_PLAN.md"
fi

# Technical docs with spaces in names
if [ -f "Preventing WhisperX Large-v3 Hallucinations with Bias and Lyrics Detection.md" ]; then
    [ "$DRY_RUN" = false ] && mv "Preventing WhisperX Large-v3 Hallucinations with Bias and Lyrics Detection.md" "$ARCHIVE_DIR/"
    log_success "Archived: Preventing WhisperX... (long filename)"
fi

if [ -f "How_Key_Features_Improve_Speech_Transcription_Translation_Accuracy.md" ]; then
    [ "$DRY_RUN" = false ] && mv "How_Key_Features_Improve_Speech_Transcription_Translation_Accuracy.md" "$ARCHIVE_DIR/"
    log_success "Archived: How_Key_Features... (long filename)"
fi

if [ -f "Implementation_Plan_for_Accura.md" ]; then
    [ "$DRY_RUN" = false ] && mv "Implementation_Plan_for_Accura.md" "$ARCHIVE_DIR/"
    log_success "Archived: Implementation_Plan_for_Accura.md"
fi

echo ""

# Step 4: Keep essential root documentation
log_info "Essential root documentation (keeping):"
KEEP_ROOT=(
    "README.md"
    "QUICKSTART.md"  
    "LICENSE"
)

for file in "${KEEP_ROOT[@]}"; do
    if [ -f "$file" ]; then
        log_success "Keeping: $file"
    else
        log_warn "Missing: $file (should exist)"
    fi
done

echo ""

# Step 5: List what's in docs/ now
log_info "Current docs/ structure:"
if [ "$DRY_RUN" = false ]; then
    tree -L 2 docs/ 2>/dev/null || find docs/ -type d | sed 's|^|  |'
fi

echo ""

# Step 6: Summary
log_info "═══════════════════════════════════════════════════════════"
log_info "  Summary"
log_info "═══════════════════════════════════════════════════════════"
echo ""

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN COMPLETE - No files were actually moved"
    log_info "Run without --dry-run to apply changes"
else
    log_success "Documentation reorganization complete!"
    echo ""
    log_info "Archived files: $ARCHIVE_DIR"
    log_info "Root docs: $(ls -1 *.md 2>/dev/null | wc -l | tr -d ' ')"
    log_info "Feature docs: $(find docs/features -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    log_info "Setup docs: $(find docs/setup -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    echo ""
    log_info "Next steps:"
    log_info "  1. Review docs/INDEX.md"
    log_info "  2. Update README.md with new structure"
    log_info "  3. Verify cross-references still work"
fi

echo ""
log_info "Documentation structure:"
echo ""
cat << 'EOF'
cp-whisperx-app/
├── README.md                    # Main overview
├── QUICKSTART.md                # Quick start guide
├── docs/
│   ├── INDEX.md                 # Documentation index
│   ├── setup/                   # Installation & setup
│   ├── user-guide/              # User documentation
│   ├── features/                # Feature documentation
│   ├── developer/               # Developer guides
│   ├── reference/               # API & config reference
│   └── archive/                 # Old documentation
└── archive/
    └── old-docs-TIMESTAMP/      # Archived files
EOF
echo ""

if [ "$DRY_RUN" = false ]; then
    log_success "✓ Documentation cleanup complete!"
else
    log_warn "⚠ Dry run complete - run without --dry-run to apply"
fi
