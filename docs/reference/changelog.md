# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-11-21

### Added
- **Anti-hallucination system**
  - Prevents repeated/incorrect transcriptions
  - Filters unreliable outputs
  - Better music/silence detection
  - Active by default for all transcriptions

- **Automated source separation**
  - Demucs integration for vocal extraction
  - Auto-enabled for all Indic languages
  - Three quality presets (fast, balanced, quality)
  - Removes 90-95% of background music

- **Documentation reorganization**
  - Complete restructure into docs/ directory
  - Clear navigation and index
  - Separated user guides, technical docs, and reference
  - Archived redundant/outdated documentation

### Fixed
- **Pipeline scripts_dir attribute error**
  - Added missing `scripts_dir` to IndicTrans2Pipeline
  - Source separation stage now works correctly

- **prepare-job.sh argument parsing**
  - Fixed `--media` flag recognition
  - Changed `python` to `python3` for correct interpreter
  - Added proper parameter handling for all flags

### Changed
- **Source separation now auto-enabled for Indic languages**
  - No manual `--source-separation` flag needed
  - Automatic for: Hindi, Tamil, Telugu, Bengali, Gujarati, etc.
  - Perfect default for Bollywood/Indian content

- **Documentation structure**
  - Root contains only README.md and LICENSE
  - All docs moved to docs/ directory
  - Clear categorization: user-guide, technical, reference
  - Added comprehensive INDEX.md

### Technical Details

#### Pipeline Fix (IndicTrans2Pipeline)
```python
# Added to __init__
self.scripts_dir = PROJECT_ROOT / "scripts"
```

#### Source Separation Auto-Enable
```bash
# In prepare-job.sh
INDIC_LANGUAGES="hi ta te bn gu kn ml mr pa ur as or ne sd si sa ks doi mni kok mai sat"
if [[ " $INDIC_LANGUAGES " =~ " $SOURCE_LANGUAGE " ]]; then
    SOURCE_SEPARATION="true"
fi
```

---

## Previous Sessions (Archived)

### 2025-11-20
- PyAnnote VAD integration
- Multi-track subtitle support
- Cache optimization
- IndicTrans2 authentication fixes

### 2025-11-19
- Initial multi-environment architecture
- WhisperX 3.7.4 upgrade
- Hardware detection system

---

## Version Numbering

This project uses semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

---

## Documentation Changes

### 2025-11-21: Major Reorganization
**Before:**
- 37+ markdown files in project root
- Redundant documentation
- No clear organization
- Hard to find information

**After:**
```
Project Root:
  README.md              # Concise overview
  LICENSE                # License file

docs/
  INDEX.md               # Complete navigation
  QUICKSTART.md          # 5-minute start
  
  user-guide/            # User documentation
    bootstrap.md
    prepare-job.md
    workflows.md
    troubleshooting.md
    features/
      anti-hallucination.md
      source-separation.md
      scene-selection.md
  
  technical/             # Technical documentation
    architecture.md
    pipeline.md
    multi-environment.md
    language-support.md
  
  reference/             # Reference documentation
    citations.md
    license.md
    changelog.md         # This file
  
  archive/               # Historical documentation
    session-notes/       # Implementation logs
    legacy/              # Outdated docs
```

---

## Breaking Changes

### None in 2025-11-21 updates
All changes are backward compatible:
- Old command syntax still works
- Existing workflows unaffected
- Source separation opt-in for non-Indic languages

---

## Migration Guide

### From Previous Versions

#### Command Line (No Changes Required)
```bash
# Old style still works
./prepare-job.sh movie.mp4 --transcribe --source-language hi

# New style recommended
./prepare-job.sh --media movie.mp4 --workflow transcribe --source-lang hi
```

#### Documentation Location
- Old: Look in project root for docs
- New: All docs in `docs/` directory
- Navigate via `docs/INDEX.md`

---

## Contributors

- Raj Patel (rpatel) - Core development, documentation

---

## Acknowledgments

### Research & Models
- WhisperX: Max Bain et al., University of Oxford
- IndicTrans2: AI4Bharat, IIT Madras
- PyAnnote: Hervé Bredin, CNRS
- Demucs: Alexandre Défossez, Meta AI

### Open Source
Built with love using open source tools.

Full citations: [citations.md](citations.md)

---

**Last Updated:** 2025-11-21
