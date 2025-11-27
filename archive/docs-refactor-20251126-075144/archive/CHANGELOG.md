# Changelog

All notable changes to cp-whisperx-app will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-11-19

### 🎉 Major Features

#### Windows Native Workflow Support
- **Added** `prepare-job.ps1` - PowerShell job preparation script
- **Added** `run-pipeline.ps1` - PowerShell pipeline orchestrator
- **Added** Complete Windows setup guide (`docs/WINDOWS_SETUP.md`)
- **Result** Windows users can now run native workflows without Docker

#### Logging Infrastructure Enhancements
- **Added** Comprehensive logging documentation
  - `docs/LOGGING_STANDARDS.md` - Complete rewrite with compliance scores
  - `docs/LOGGING_TROUBLESHOOTING.md` - 500+ line troubleshooting guide
  - `LOGGING_ANALYSIS_REPORT.md` - Detailed compliance analysis
- **Added** Logging section to main README
- **Improved** Developer experience with centralized logging documentation

#### Log Management Tools
- **Added** `tools/rotate-logs.sh` - Bash log rotation with compression
- **Added** `tools/rotate-logs.ps1` - PowerShell log rotation
- **Added** `tools/analyze-logs.py` - Python log aggregator and analyzer
- **Added** `tools/validate-compliance.py` - Logging compliance validator

### ✨ Enhancements

#### Cross-Platform Parity
- **Achieved** 100% bash-PowerShell script parity
- **Improved** Consistent logging across all languages (bash, PowerShell, Python)
- **Updated** All scripts now use common logging frameworks

#### Documentation
- **Added** Windows-specific setup instructions
- **Added** GPU acceleration guides (CUDA for Windows)
- **Added** Platform comparison matrices
- **Added** Quick reference cards
- **Added** Implementation summary documentation

#### Compliance
- **Achieved** 98% logging compliance score
- **Updated** `install-mlx.sh` to use common logging
- **Standardized** All main scripts follow logging standards

### 📚 Documentation

#### New Documentation
- `docs/WINDOWS_SETUP.md` - Complete Windows installation guide
- `docs/LOGGING_TROUBLESHOOTING.md` - Comprehensive troubleshooting
- `docs/IMPLEMENTATION_SUMMARY_LOGGING.md` - Implementation details
- `LOGGING_ANALYSIS_REPORT.md` - Compliance analysis report
- `QUICK_REFERENCE.md` - Quick reference cards

#### Updated Documentation
- `README.md` - Added "Logging & Debugging" section
- `docs/LOGGING_STANDARDS.md` - Complete rewrite with current state

### 🔧 Bug Fixes
- Fixed log file encoding issues on Windows (UTF-8 support)
- Fixed PowerShell color output compatibility
- Fixed log file auto-creation in all scripts

### 🚀 Performance
- Log rotation reduces disk usage automatically
- Log aggregation enables faster multi-job analysis
- Optimized log file reuse for same-day jobs

---

## [1.0.0] - 2024-11-18

### Initial Release

#### Core Features
- Multi-language ASR (22 Indian languages + English)
- WhisperX integration for fast transcription
- IndicTrans2 for high-quality Indian language translation
- Speaker diarization with PyAnnote
- Bias injection for name/term correction
- Lyrics detection for musical content
- Hardware auto-detection (MPS/CUDA/CPU)
- MLX acceleration for Apple Silicon

#### Workflows
- **Transcribe:** Audio → Text with timestamps
- **Translate:** Text → English subtitles
- **Subtitle:** Complete dual-subtitle generation

#### Platform Support
- macOS (native with MPS acceleration)
- Linux (Docker with CUDA/CPU)
- Windows (Docker only)

#### Documentation
- Complete architecture documentation
- MLX acceleration guide
- IndicTrans2 workflow guide
- Configuration reference

---

## [Unreleased]

### Planned Features
- [ ] Web-based log viewer
- [ ] Real-time pipeline monitoring dashboard
- [ ] Integrated testing framework
- [ ] CI/CD pipeline integration
- [ ] Structured JSON logging option
- [ ] Log shipping to central server

### Under Consideration
- [ ] Support for more target languages
- [ ] Video subtitle burning (hardcoded subs)
- [ ] Batch job processing
- [ ] REST API interface
- [ ] Cloud deployment guides

---

## Version History Summary

| Version | Date | Description |
|---------|------|-------------|
| 1.1.0 | 2025-11-19 | Windows native support, logging enhancements, 100% cross-platform parity |
| 1.0.0 | 2024-11-18 | Initial release with core ASR/translation features |

---

## Upgrade Guide

### From 1.0.0 to 1.1.0

**No breaking changes** - This is a backward-compatible release.

#### For Existing Users (macOS/Linux)
1. Pull latest changes: `git pull origin main`
2. No action required - existing workflows continue to work
3. Optional: Review new logging documentation

#### For New Windows Users
1. Follow the new Windows setup guide: `docs/WINDOWS_SETUP.md`
2. Install PowerShell 7+, Python, FFmpeg
3. Run `.\scripts\bootstrap.ps1`
4. Use PowerShell scripts: `.\prepare-job.ps1`, `.\run-pipeline.ps1`

#### For All Users - New Features
1. **Log Rotation:** Set up automated log rotation
   ```bash
   # Bash (macOS/Linux)
   ./tools/rotate-logs.sh --keep-days 30
   
   # PowerShell (Windows)
   .\tools\rotate-logs.ps1 -KeepDays 30
   ```

2. **Log Analysis:** Analyze logs from multiple jobs
   ```bash
   python tools/analyze-logs.py --days 7 --json analysis.json
   ```

3. **Compliance Validation:** Check script compliance
   ```bash
   python tools/validate-compliance.py
   ```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code standards (including logging standards)

---

## Support

- **Issues:** https://github.com/yourusername/cp-whisperx-app/issues
- **Discussions:** https://github.com/yourusername/cp-whisperx-app/discussions
- **Documentation:** See `docs/` directory

---

**Maintained by:** CP-WhisperX-App Team  
**License:** See [LICENSE](LICENSE)
