# User Guide

Complete guide for using the WhisperX Speech Processing Pipeline.

## Overview

This guide covers everything you need to know to effectively use the pipeline:

- **Setup**: Getting started with the environment
- **Configuration**: Customizing pipeline behavior
- **Workflows**: Common usage patterns
- **Troubleshooting**: Solving common issues

## Documentation Structure

### Getting Started

1. **[Bootstrap Guide](bootstrap.md)** - Initial environment setup
2. **[Prepare Job Guide](prepare-job.md)** - Configuring your jobs
3. **[Workflows](workflows.md)** - Common usage patterns

### Configuration

- **[Configuration Guide](configuration.md)** - Complete configuration reference
- **[Glossary Builder](glossary-builder.md)** - Creating custom glossaries

### Support

- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Quick Navigation

### By Task

- **First Time Setup**: Start with [Bootstrap](bootstrap.md)
- **Processing Audio**: See [Workflows](workflows.md)
- **Custom Terms**: Check [Glossary Builder](glossary-builder.md)
- **Problems**: Visit [Troubleshooting](troubleshooting.md)
- **Advanced Options**: Read [Configuration](configuration.md)

### By Experience Level

**Beginners**: 
1. [Bootstrap](bootstrap.md)
2. [Quick Start](../QUICKSTART.md)
3. [Workflows](workflows.md)

**Intermediate Users**:
1. [Configuration](configuration.md)
2. [Glossary Builder](glossary-builder.md)
3. [Troubleshooting](troubleshooting.md)

**Advanced Users**:
1. [Configuration](configuration.md) - All options
2. [Technical Architecture](../technical/architecture.md)
3. [Developer Guide](../DEVELOPER_GUIDE.md)

## Key Concepts

### Pipeline Stages

The pipeline processes audio through three main stages:

1. **Transcribe**: Speech-to-text conversion
   - WhisperX large-v3 model
   - Forced alignment for accurate timing
   - Speaker diarization
   - Hallucination and lyrics detection

2. **Translate**: Multi-language translation
   - IndicTrans2 for Indian languages
   - Google Translate for other languages
   - Glossary-based term enforcement
   - Context-aware retranslation

3. **Subtitles**: Professional subtitle generation
   - SRT and VTT formats
   - Speaker labels
   - Configurable timing and formatting
   - Metadata embedding

### Configuration Hierarchy

Pipeline behavior is controlled through:

1. **Global Configuration** (`config/pipeline.conf`)
   - Default settings for all jobs
   - Environment-specific settings
   - Model configurations

2. **Job Configuration** (created by `prepare-job.sh`)
   - Per-file settings
   - Overrides global defaults
   - Stored in `config/job_<name>.conf`

3. **Command-line Options**
   - Runtime overrides
   - Stage-specific execution
   - Debugging options

### Glossary System

Glossaries enforce custom terminology:

- **Format**: Pipe-separated (`source|target`)
- **Usage**: Per-job or global
- **Auto-generation**: From translations
- **Retranslation**: Automatic term correction

See [Glossary Builder](glossary-builder.md) for details.

## Common Workflows

### Standard Processing

```bash
# Setup (one time)
./bootstrap.sh

# For each audio file
./prepare-job.sh audio.mp3
./run-pipeline.sh audio.mp3
```

### With Translation

```bash
./prepare-job.sh --source-lang hi --target-lang en audio.mp3
./run-pipeline.sh audio.mp3
```

### With Custom Glossary

```bash
./prepare-job.sh --glossary glossary/terms.txt audio.mp3
./run-pipeline.sh audio.mp3
```

See [Workflows](workflows.md) for more examples.

## File Locations

### Input
- **Audio files**: `in/` directory (or any path)
- **Glossaries**: `glossary/` directory

### Configuration
- **Global config**: `config/pipeline.conf`
- **Job configs**: `config/job_*.conf`
- **Environment**: `.env` file (auto-generated)

### Output
- **All outputs**: `out/<filename>/`
- **Transcripts**: `out/<filename>/*_transcript.*`
- **Translations**: `out/<filename>/*_translation.txt`
- **Subtitles**: `out/<filename>/*_subtitles.*`

### Logs
- **Pipeline logs**: `logs/pipeline.log`
- **Stage logs**: `logs/<stage>.log`

## Best Practices

### Audio Files

- **Formats**: MP3, WAV, M4A, FLAC recommended
- **Quality**: Higher quality = better transcription
- **Size**: No strict limits, but consider processing time
- **Storage**: Keep originals, outputs are regeneratable

### Configuration

- **Start with defaults**: Modify only when needed
- **Use job configs**: For per-file customization
- **Document changes**: Comment configuration files
- **Test settings**: Start with small files

### Glossaries

- **Be specific**: Include context-specific terms
- **Use consistently**: Same glossary for related files
- **Review auto-generated**: Check and refine
- **Maintain centrally**: Keep in `glossary/` directory

### Performance

- **Batch processing**: Process multiple files sequentially
- **Resource management**: Don't overload beam_size/best_of
- **Disk space**: Monitor output directory size
- **Clean up**: Archive old outputs periodically

## Tips and Tricks

### Faster Processing

- Use appropriate hardware (MLX on Mac, CUDA on Linux)
- Reduce `beam_size` for faster (but less accurate) results
- Process only needed stages
- Use lower quality audio for testing

### Better Accuracy

- Increase `beam_size` and `best_of` (slower)
- Use appropriate source language code
- Provide good quality audio
- Use glossaries for technical terms

### Debugging

- Check logs in `logs/` directory
- Run stages individually to isolate issues
- Use verbose logging (if available)
- Test with small audio clips first

## Getting Help

### Documentation

- **[Documentation Index](../INDEX.md)** - All documentation
- **[Quick Start](../QUICKSTART.md)** - 5-minute start
- **[Troubleshooting](troubleshooting.md)** - Problem solving

### Technical Details

- **[Architecture](../technical/architecture.md)** - System design
- **[Pipeline](../technical/pipeline.md)** - Stage details
- **[Multi-Environment](../technical/multi-environment.md)** - Platform support

### Developer Resources

- **[Developer Guide](../DEVELOPER_GUIDE.md)** - Contribution guide
- **[Process](../PROCESS.md)** - Development process

## Next Steps

Choose your path:

- **New User**: Read [Bootstrap](bootstrap.md) → [Quick Start](../QUICKSTART.md)
- **Configure Pipeline**: Check [Configuration](configuration.md)
- **Advanced Usage**: See [Workflows](workflows.md)
- **Troubleshoot**: Visit [Troubleshooting](troubleshooting.md)
- **Contribute**: Read [Developer Guide](../DEVELOPER_GUIDE.md)

---

**Navigation**: [Home](../../README.md) | [Documentation Index](../INDEX.md) | [Quick Start](../QUICKSTART.md)
