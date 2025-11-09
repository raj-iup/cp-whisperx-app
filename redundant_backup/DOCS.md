# Documentation Map

**Quick navigation to all CP-WhisperX-App documentation**

---

## 🚀 Start Here

- **[README.md](README.md)** - Project overview and quick intro
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[docs/INDEX.md](docs/INDEX.md)** - Complete documentation index

---

## 📖 Core Documentation

### Setup
- **[docs/BOOTSTRAP.md](docs/BOOTSTRAP.md)** - Environment setup
- **[docs/CROSS_PLATFORM_GUIDE.md](CROSS_PLATFORM_GUIDE.md)** - Platform-specific setup (macOS/Windows/Linux)

### Understanding the System
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[docs/WORKFLOW.md](docs/WORKFLOW.md)** - Pipeline workflow
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Configuration reference

### Using the System
- **[docs/RUNNING.md](docs/RUNNING.md)** - Running the pipeline
- **[docs/RESUME.md](docs/RESUME.md)** - Resume interrupted jobs
- **[docs/GLOSSARY_SYSTEM.md](docs/GLOSSARY_SYSTEM.md)** - Glossary features (NEW ✨)

### Troubleshooting
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues
- **[docs/FAQ.md](docs/FAQ.md)** - Frequently asked questions

---

## 🎯 By Task

| I want to... | Go to... |
|--------------|----------|
| Get started quickly | [QUICKSTART.md](docs/QUICKSTART.md) |
| Understand how it works | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Set up my environment | [BOOTSTRAP.md](docs/BOOTSTRAP.md) |
| Configure the pipeline | [CONFIGURATION.md](docs/CONFIGURATION.md) |
| Process my first movie | [RUNNING.md](docs/RUNNING.md) |
| Use glossary features | [GLOSSARY_SYSTEM.md](docs/GLOSSARY_SYSTEM.md) |
| Fix an error | [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Resume a failed job | [RESUME.md](docs/RESUME.md) |

---

## 📁 Repository Structure

```
cp-whisperx-app/
├── README.md                    # Project overview
├── DOCS.md                      # This file
├── IMPROVEMENT-PLAN.md          # Roadmap
├── CROSS_PLATFORM_GUIDE.md      # Platform setup
│
├── docs/                        # 📚 Documentation
│   ├── INDEX.md                 # Complete documentation index
│   ├── QUICKSTART.md            # Quick start guide
│   ├── ARCHITECTURE.md          # System architecture
│   ├── WORKFLOW.md              # Pipeline workflow
│   ├── BOOTSTRAP.md             # Environment setup
│   ├── CONFIGURATION.md         # Config reference
│   ├── RUNNING.md               # Running the pipeline
│   ├── RESUME.md                # Resume jobs
│   ├── GLOSSARY_SYSTEM.md       # Glossary documentation ✨
│   ├── TROUBLESHOOTING.md       # Troubleshooting guide
│   ├── FAQ.md                   # FAQ
│   ├── PERFORMANCE.md           # Performance tuning
│   ├── API_REFERENCE.md         # API reference
│   ├── CONTRIBUTING.md          # Contribution guide
│   ├── CHANGELOG.md             # Version history
│   └── history/                 # Historical docs (archived)
│
├── scripts/                     # Pipeline scripts
├── docker/                      # Docker stage containers
├── shared/                      # Shared Python modules
├── config/                      # Configuration templates
├── glossary/                    # Glossary system ✨
│   ├── hinglish_master.tsv      # Master glossary
│   └── prompts/                 # Movie-specific prompts
└── tools/                       # Utility scripts
```

---

## 🌟 What's New

### Recent Documentation Updates (2025-11-09)

✅ **[GLOSSARY_SYSTEM.md](docs/GLOSSARY_SYSTEM.md)** - Complete glossary documentation
  - Basic usage guide
  - 7 advanced strategies
  - 18+ Bollywood movie prompts
  - Character profiles & regional variants
  - Configuration & troubleshooting

✅ **Documentation Consolidation**
  - All docs organized by topic
  - Clear navigation structure
  - Historical docs archived
  - Updated INDEX.md

✅ **[CROSS_PLATFORM_GUIDE.md](CROSS_PLATFORM_GUIDE.md)** - Enhanced platform support
  - macOS (MPS acceleration)
  - Windows (CUDA/CPU)
  - Linux (CUDA/CPU)

---

## 🔍 Finding Information

### By Topic
Use **[docs/INDEX.md](docs/INDEX.md)** - organized by topic with quick links

### By Task
Check the "I want to..." section above or in INDEX.md

### Search
```bash
# Search all documentation
grep -r "your topic" docs/*.md

# Search configuration docs
grep -r "GLOSSARY_STRATEGY" docs/*.md config/

# Search troubleshooting
grep -r "error message" docs/TROUBLESHOOTING.md
```

---

## 📚 Learning Path

### Beginner (1-2 hours)
1. [README.md](README.md) - 5 min
2. [QUICKSTART.md](docs/QUICKSTART.md) - 30 min
3. [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 15 min
4. Process test clip - 30 min
5. [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 10 min

### Intermediate (3-4 hours)
1. Complete Beginner path
2. [WORKFLOW.md](docs/WORKFLOW.md) - 30 min
3. [CONFIGURATION.md](docs/CONFIGURATION.md) - 20 min
4. [GLOSSARY_SYSTEM.md](docs/GLOSSARY_SYSTEM.md) - 60 min
5. Process full movie - 90 min

### Advanced (1-2 days)
1. Complete Intermediate path
2. Deep dive [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 60 min
3. Master [GLOSSARY_SYSTEM.md](docs/GLOSSARY_SYSTEM.md) - 120 min
4. Create custom prompts - 60 min
5. [PERFORMANCE.md](docs/PERFORMANCE.md) - 60 min
6. Process multiple films - 4+ hours

---

## 🎯 Documentation Goals

This documentation structure aims to:

✅ Get you started in < 5 minutes  
✅ Explain every feature comprehensively  
✅ Provide troubleshooting for common issues  
✅ Support all platforms equally  
✅ Enable easy navigation and discovery  
✅ Maintain clear, up-to-date information  

---

## 📧 Need Help?

1. Check **[FAQ.md](docs/FAQ.md)**
2. Review **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**
3. Search documentation with grep
4. Check GitHub issues (if available)
5. File new issue with details

---

## 🤝 Contributing

Want to improve documentation? See **[CONTRIBUTING.md](docs/CONTRIBUTING.md)**

Found outdated info? File an issue or submit a pull request!

---

**Last Updated**: 2025-11-09  
**Documentation Version**: 2.0 (Consolidated)  
**Project Version**: 1.0
