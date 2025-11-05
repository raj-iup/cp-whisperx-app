# Docker Dependency Version Management

**Centralized version management for all Docker images**

Last updated: 2025-11-05

---

## Base Dependencies

### Python
- **Version**: 3.11

### Core Scientific Computing
- numpy==1.24.3
- scipy==1.11.4

### Audio Processing
- soundfile==0.12.1
- librosa==0.10.1

---

## PyTorch Ecosystem

### PyTorch (CUDA 12.1)
- torch==2.1.0+cu121
- torchaudio==2.1.0+cu121

**Installation**: `--index-url https://download.pytorch.org/whl/cu121`

---

## Whisper Ecosystem

### WhisperX and Dependencies
- whisperx==3.7.2
- faster-whisper==1.2.0
- ctranslate2==4.6.0

### Transformers
- transformers==4.57.1
- huggingface-hub==0.20.3
- sentencepiece==0.1.99

---

## Diarization & VAD

### PyAnnote
- pyannote.audio==3.4.0
- pyannote.core==5.0.0
- pyannote.database==5.1.3
- pyannote.metrics==3.2.1
- pyannote.pipeline==3.0.1

### Supporting Libraries
- pytorch-lightning==2.5.5
- torchmetrics==1.8.2
- speechbrain==1.0.1

---

## NER (Named Entity Recognition)

### spaCy
- spacy==3.8.7
- rapidfuzz==3.0.0

---

## Metadata & Utilities

### TMDB
- tmdbv3api==1.9.0

### Subtitle Handling
- pysrt==1.1.2
- pysubs2==1.8.0

### Environment
- python-dotenv==1.2.1

### Progress & Formatting
- tqdm==4.66.0
- rich==14.2.0

### File Formats
- protobuf==3.20.3

---

## Compatibility Matrix

### PyTorch 2.1.0 Compatibility
✅ pyannote.audio 3.4.0  
✅ whisperx 3.7.2  
✅ pytorch-lightning 2.5.5  
✅ transformers 4.57.1

### NumPy 1.24.3 Compatibility
✅ Compatible with all packages  
⚠️ Some packages require <2.0.0

---

## Version Update Checklist

When updating versions:

1. ✅ Update this file FIRST
2. ✅ Update `docker/requirements-common.txt`
3. ✅ Update stage-specific requirements files
4. ✅ Test compatibility matrix
5. ✅ Update `docs/DOCKER_OPTIMIZATION_RECOMMENDATIONS.md`
6. ✅ Commit with detailed changelog

---

## Notes

- All Docker images reference these pinned versions
- Keep versions synchronized across all stages
- Test thoroughly after version updates
