# .gitignore Configuration for Native MPS Pipeline

## Overview

A comprehensive `.gitignore` file configured specifically for the Native MPS Pipeline, ensuring sensitive data, build artifacts, and large files are excluded from version control while maintaining the essential project structure.

## What's Ignored

### 🔐 Secrets & Credentials
```
config/secrets.json       # API keys (TMDB, HuggingFace)
.env                      # Environment variables
*.key, *.pem             # Private keys
```

### 🐍 Python Artifacts
```
__pycache__/             # Compiled Python bytecode
*.pyc, *.pyo, *.pyd     # Python cache files
native/venvs/            # All 10 virtual environments (~2GB+)
```

### 📁 Data Directories
```
in/                      # Input video files
out/                     # Output processed videos
logs/                    # Pipeline execution logs
temp/                    # Temporary processing files
```

### 🎬 Media Files
```
*.mp4, *.mkv, *.avi     # Video files
*.wav                    # Audio files
*.srt, *.vtt            # Subtitle files
```

### 🤖 ML Models
```
*.pt, *.pth, *.onnx     # Downloaded model files
.cache/                  # Model cache (~5GB+)
models/                  # Model storage
```

### 💻 IDE & OS Files
```
.vscode/, .idea/        # IDE settings
.DS_Store               # macOS metadata
Thumbs.db               # Windows thumbnails
```

## What's Tracked

### ✅ Essential Files (Always Committed)
```
.gitkeep files          # Preserve directory structure
*.example files         # Configuration templates
*.template files        # Environment templates
*.py                    # Python source code
*.sh                    # Shell scripts
*.txt                   # Requirements files
*.md                    # Documentation
```

### 📂 Directory Structure Preserved
```
logs/.gitkeep           # Empty logs directory
in/.gitkeep             # Empty input directory
out/.gitkeep            # Empty output directory
temp/.gitkeep           # Empty temp directory
```

## Usage

### Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd cp-whisperx-app

# Directory structure is already created via .gitkeep files
ls -la logs/ in/ out/ temp/

# Copy example files and configure
cp config/secrets.example.json config/secrets.json
nano config/secrets.json  # Add your API keys
```

### Development Workflow
```bash
# Add input videos (automatically ignored)
cp ~/Movies/video.mp4 in/

# Run pipeline (outputs automatically ignored)
./native/pipeline.sh "in/video.mp4"

# Only commit code changes
git add native/scripts/
git commit -m "Update ASR configuration"
```

### Checking Ignored Files
```bash
# Test if a file is ignored
git check-ignore path/to/file

# List all ignored files in current directory
git status --ignored

# See why a file is ignored
git check-ignore -v path/to/file
```

## File Size Benefits

With this `.gitignore`, the following are **excluded** from git:

| Category | Size | Files |
|----------|------|-------|
| Virtual Environments | ~2-3 GB | `native/venvs/*` |
| Model Cache | ~5-10 GB | `.cache/torch/*` |
| Input Videos | Variable | `in/*.mp4` |
| Output Videos | Variable | `out/**/*.mp4` |
| Log Files | ~10-100 MB | `logs/*.log` |
| **Total Saved** | **~10-20 GB+** | - |

This keeps your repository lightweight and fast!

## Security Notes

### 🚨 Never Commit These
- `config/secrets.json` - Contains API keys
- `.env` files - May contain sensitive configuration
- `*.key`, `*.pem` - Private encryption keys

### ✅ Safe to Commit
- `config/secrets.example.json` - Template with no real keys
- `.env.example` - Template with placeholder values
- All source code (`.py`, `.sh`)
- Documentation (`.md`)

## Troubleshooting

### File Not Being Ignored

```bash
# Check if file matches ignore pattern
git check-ignore -v path/to/file

# Force remove if already tracked
git rm --cached path/to/file
git commit -m "Remove tracked file"
```

### Directory Not Being Preserved

```bash
# Ensure .gitkeep exists
touch directory/.gitkeep
git add directory/.gitkeep
```

### Reset All Ignored Files

```bash
# WARNING: This removes ALL ignored files
git clean -fdX

# Preview what would be removed
git clean -ndX
```

## Maintenance

### Update .gitignore

```bash
# Edit .gitignore
nano .gitignore

# Test changes
git check-ignore -v path/to/test/file

# Commit changes
git add .gitignore
git commit -m "Update .gitignore rules"
```

### Clean Up Already-Tracked Files

If files are already tracked but should be ignored:

```bash
# Remove from git but keep locally
git rm --cached -r native/venvs/
git commit -m "Remove venvs from tracking"
```

## Best Practices

1. **Always use .gitkeep** to preserve empty directories
2. **Never commit secrets** - use `.example` files instead
3. **Keep media files local** - they're too large for git
4. **Commit requirement files** - for reproducible environments
5. **Test ignore patterns** before committing sensitive files

## Pattern Reference

### Directory Patterns
```gitignore
logs/              # Ignores entire directory
logs/*             # Ignores contents but not directory itself
logs/*.log         # Ignores only .log files in logs/
logs/**/*.log      # Ignores .log files in logs/ and subdirectories
```

### Negation Patterns
```gitignore
logs/*             # Ignore all contents
!logs/.gitkeep     # But track .gitkeep file
```

### Wildcard Patterns
```gitignore
*.log              # All .log files anywhere
**/*.pyc           # All .pyc files in any subdirectory
temp*              # Files/dirs starting with temp
```

## Verification Script

Test your .gitignore configuration:

```bash
#!/bin/bash
echo "Testing .gitignore rules..."

# Files that should be ignored
test_ignored=(
    "logs/test.log"
    "in/test.mp4"
    "out/test.mp4"
    "config/secrets.json"
    "native/venvs/"
    ".DS_Store"
)

# Files that should be tracked
test_tracked=(
    "logs/.gitkeep"
    "in/.gitkeep"
    "config/secrets.example.json"
    "native/scripts/01_demux.py"
)

for file in "${test_ignored[@]}"; do
    if git check-ignore "$file" > /dev/null 2>&1; then
        echo "✅ $file - correctly ignored"
    else
        echo "❌ $file - ERROR: not ignored"
    fi
done

for file in "${test_tracked[@]}"; do
    if git check-ignore "$file" > /dev/null 2>&1; then
        echo "❌ $file - ERROR: incorrectly ignored"
    else
        echo "✅ $file - correctly tracked"
    fi
done
```

---

**Created for:** Native MPS Pipeline  
**Last Updated:** 2025-10-30  
**Tested With:** Git 2.39+
