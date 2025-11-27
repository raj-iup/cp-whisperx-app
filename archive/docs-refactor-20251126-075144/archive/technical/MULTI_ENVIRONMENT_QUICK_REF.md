# Multi-Environment Quick Reference

## Commands

### Setup
```bash
./bootstrap.sh                    # Create all environments
./bootstrap.sh --env whisperx     # Create specific environment
./bootstrap.sh --check            # Check status
./bootstrap.sh --clean            # Remove all environments
```

### Environment Info
```bash
# List environments
python shared/environment_manager.py list

# Check specific environment
python shared/environment_manager.py check --env whisperx

# Get environment info
python shared/environment_manager.py info --env indictrans2

# Validate workflow requirements
python shared/environment_manager.py validate --workflow subtitle
```

## Environment Mapping

### Stages
| Stage | Environment |
|-------|-------------|
| demux | whisperx |
| asr | whisperx |
| alignment | whisperx |
| export_transcript | whisperx |
| load_transcript | indictrans2 |
| indictrans2_translation_* | indictrans2 |
| subtitle_generation_* | common |
| mux | common |

### Workflows
| Workflow | Environments |
|----------|--------------|
| transcribe | whisperx |
| translate | indictrans2, common |
| subtitle | whisperx, indictrans2, common |

## Troubleshooting

### Environment not found
```bash
./bootstrap.sh --env <name>
```

### Dependency conflict
```bash
./bootstrap.sh --clean
./bootstrap.sh --env <name>
```

### Check Python path
```bash
python shared/environment_manager.py python-path --env whisperx
```

## Files

- `config/hardware_cache.json` - Configuration
- `requirements-whisperx.txt` - WhisperX deps
- `requirements-indictrans2.txt` - IndicTrans2 deps
- `requirements-common.txt` - Utility deps
- `venv/whisperx/` - WhisperX environment
- `venv/indictrans2/` - IndicTrans2 environment
- `venv/common/` - Common environment
