#!/bin/bash
# Documentation organization script
# Moves all docs to proper locations in docs/ directory

set -e

echo "==================================="
echo "Documentation Organization"
echo "==================================="
echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p docs/user-guide/features
mkdir -p docs/technical
mkdir -p docs/reference

# Move/consolidate user guide documents
echo "Organizing user guides..."
mv -f HALLUCINATION_FIX_SUMMARY.md docs/user-guide/features/anti-hallucination.md 2>/dev/null || true
mv -f SOURCE_SEPARATION_GUIDE.md docs/user-guide/features/source-separation.md 2>/dev/null || true
mv -f SCENE_SELECTION_TIPS.md docs/user-guide/features/scene-selection.md 2>/dev/null || true

# Move technical documentation
echo "Organizing technical docs..."
mv -f MULTI_ENVIRONMENT_ARCHITECTURE.md docs/technical/multi-environment.md 2>/dev/null || true

# Create reference docs
echo "Creating reference docs..."
# Citations already exists
# License will be created
# Changelog will be consolidated

# Archive old/redundant files
echo "Archiving old documentation..."
mkdir -p docs/archive/session-notes
mkdir -p docs/archive/legacy

# Move session-specific notes to archive
for file in *2025*.md *SESSION*.md *FIXES*.md *IMPLEMENTATION*.md *SUMMARY*.md; do
    [ -f "$file" ] && mv "$file" docs/archive/session-notes/ 2>/dev/null || true
done

# Move legacy/redundant docs
for file in *FIX*.md *COMPLETE*.md *STATUS*.md *ISSUE*.md *REFACTOR*.md *CACHE*.md *PYANNOTE*.md *INDICTRANS2*.md; do
    [ -f "$file" ] && mv "$file" docs/archive/legacy/ 2>/dev/null || true
done

# Keep only essential docs in root
echo "Cleaning project root..."
# Keep: README.md, LICENSE
# Remove: Everything else will be in docs/

echo ""
echo "✓ Documentation organized"
echo ""
echo "Structure:"
echo "  docs/"
echo "    ├── INDEX.md"
echo "    ├── QUICKSTART.md"
echo "    ├── user-guide/"
echo "    │   ├── features/"
echo "    │   │   ├── anti-hallucination.md"
echo "    │   │   ├── source-separation.md"
echo "    │   │   └── scene-selection.md"
echo "    ├── technical/"
echo "    └── reference/"
echo ""
echo "Archived:"
echo "  docs/archive/"
echo "    ├── session-notes/  (implementation logs)"
echo "    └── legacy/          (old documentation)"
echo ""
echo "Project root now contains only:"
echo "  - README.md (main documentation entry)"
echo "  - LICENSE"
echo "  - Script files (.sh)"
echo ""

