# Documentation Rebuild Plan

## Current State (Problems)

1. **Too many root-level MD files** (28 files)
2. **Duplicate/overlapping content**
3. **No clear documentation hierarchy**
4. **Hard to find information**
5. **Multiple "COMPLETE" status files**
6. **Inconsistent naming conventions**

## New Structure (Clean & Organized)

```
cp-whisperx-app/
├── README.md                          # Main project overview
├── QUICKSTART.md                      # 5-minute getting started
├── CHANGELOG.md                       # Version history
├── docs/
│   ├── INDEX.md                       # Documentation index
│   ├── setup/
│   │   ├── INSTALLATION.md            # Bootstrap, requirements
│   │   ├── CONFIGURATION.md           # Config files, secrets
│   │   ├── MODEL_CACHING.md           # Pre-caching models
│   │   └── HARDWARE.md                # GPU/CPU requirements
│   ├── user-guide/
│   │   ├── WORKFLOWS.md               # Transcribe, translate, subtitle
│   │   ├── PREPARE_JOB.md             # Job preparation
│   │   ├── RUN_PIPELINE.md            # Pipeline execution
│   │   ├── SUBTITLES.md               # Subtitle generation
│   │   └── TROUBLESHOOTING.md         # Common issues
│   ├── features/
│   │   ├── HYBRID_TRANSLATION.md      # IndicTrans2 + LLM
│   │   ├── LYRICS_DETECTION.md        # Song detection
│   │   ├── HALLUCINATION_REMOVAL.md   # Anti-hallucination
│   │   ├── SOURCE_SEPARATION.md       # Demucs integration
│   │   ├── GLOSSARY.md                # Name/location glossary
│   │   └── NER_CORRECTION.md          # Name entity correction
│   ├── developer/
│   │   ├── ARCHITECTURE.md            # System design
│   │   ├── DEVELOPER_GUIDE.md         # Coding standards
│   │   ├── PIPELINE_STAGES.md         # Stage details
│   │   ├── ADDING_FEATURES.md         # How to extend
│   │   └── TESTING.md                 # Test procedures
│   ├── reference/
│   │   ├── API.md                     # Python API
│   │   ├── CONFIG_REFERENCE.md        # All config options
│   │   ├── ENVIRONMENT_VARS.md        # Environment variables
│   │   └── CLI_REFERENCE.md           # Command-line tools
│   └── archive/                       # Old documentation
└── scripts/
    └── organize-docs.sh               # Documentation organizer
```

## Migration Plan

### Phase 1: Archive Old Docs
Move duplicate/obsolete docs to archive:
- PHASE_1_*.md → archive/
- *_COMPLETE.md → archive/
- IMPLEMENTATION_*.md → archive/
- INTEGRATION_*.md → archive/

### Phase 2: Consolidate Core Docs
Merge and clean:
- All hybrid translation docs → docs/features/HYBRID_TRANSLATION.md
- All lyrics detection docs → docs/features/LYRICS_DETECTION.md  
- All setup docs → docs/setup/
- All user guides → docs/user-guide/

### Phase 3: Create New Structure
Build comprehensive, non-redundant docs:
- Clear hierarchy
- No duplication
- Easy navigation
- Consistent style

### Phase 4: Update Root Files
Keep only essentials in root:
- README.md (overview, badges, quick links)
- QUICKSTART.md (5-minute start)
- CHANGELOG.md (version history)
- LICENSE (if exists)

## Documentation Standards

### File Naming
- Use CAPS for major docs (README.md, QUICKSTART.md)
- Use sentence-case for specific features (Hybrid_Translation.md)
- No spaces in filenames
- Use hyphens for multi-word (Multi-Environment-Setup.md)

### Content Structure
1. **Title & Summary** (what & why)
2. **Quick Example** (working code/command)
3. **Detailed Guide** (how-to, step-by-step)
4. **Configuration** (all options)
5. **Troubleshooting** (common issues)
6. **See Also** (related docs)

### Style Guide
- Use headers consistently (H1=Title, H2=Sections, H3=Subsections)
- Include code blocks with language tags
- Use tables for comparisons
- Include examples for every feature
- Keep it concise (link to details, don't duplicate)

## Implementation

Run: `./scripts/organize-docs.sh`

This will:
1. Create new structure
2. Move files to archive
3. Generate consolidated docs
4. Update cross-references
5. Create INDEX.md

## Timeline

- Archive old docs: Immediate
- Create new structure: 30 minutes
- Consolidate content: 2 hours
- Review & polish: 1 hour
- **Total: ~4 hours**

