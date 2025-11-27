# Citations and Acknowledgments

**CP-WhisperX-App** - Multi-Environment ASR, Translation & Subtitle Pipeline

---

## Core Technologies

### 1. WhisperX - Word-Level ASR
**Citation**:
```bibtex
@article{bain2022whisperx,
  title={WhisperX: Time-Accurate Speech Transcription of Long-Form Audio},
  author={Bain, Max and Huh, Jaesung and Han, Tengda and Zisserman, Andrew},
  journal={INTERSPEECH 2023},
  year={2023}
}
```

**License**: BSD-4-Clause  
**Repository**: https://github.com/m-bain/whisperX  
**Usage**: Automatic speech recognition with word-level timestamps

---

### 2. Whisper (OpenAI) - Foundation Model
**Citation**:
```bibtex
@article{radford2022whisper,
  title={Robust Speech Recognition via Large-Scale Weak Supervision},
  author={Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya},
  journal={arXiv preprint arXiv:2212.04356},
  year={2022}
}
```

**License**: MIT  
**Repository**: https://github.com/openai/whisper  
**Usage**: Base ASR model (large-v3) for transcription

---

### 3. IndicTrans2 - Indic Language Translation
**Citation**:
```bibtex
@article{gala2023indictrans,
  title={IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22 Scheduled Indian Languages},
  author={Gala, Jay and Chitale, Pranjal A and Raghavan, AK and Gumma, Varun and Kunchukuttan, Anoop and Golla, Pratyush and Doddapaneni, Sumanth and Bhattacharyya, Aswanth Karthik and Khapra, Mitesh M and Bapi, Raj and others},
  journal={Transactions on Machine Learning Research},
  year={2023}
}
```

**License**: MIT  
**Repository**: https://github.com/AI4Bharat/IndicTrans2  
**Hugging Face Models**:
- `ai4bharat/indictrans2-en-indic-1B` (Indic→English)
- `ai4bharat/indictrans2-indic-indic-1B` (Indic→Indic)

**Usage**: High-quality translation for 22 Indian languages

---

### 4. NLLB-200 - Universal Translation
**Citation**:
```bibtex
@article{nllb2022,
  title={No Language Left Behind: Scaling Human-Centered Machine Translation},
  author={NLLB Team and others},
  journal={arXiv preprint arXiv:2207.04672},
  year={2022}
}
```

**License**: CC-BY-NC 4.0  
**Repository**: https://github.com/facebookresearch/fairseq/tree/nllb  
**Hugging Face Model**: `facebook/nllb-200-distilled-600M`  
**Usage**: Translation for 200+ languages (non-Indic)

---

### 5. Faster-Whisper - CTranslate2 Backend
**Citation**:
```bibtex
@misc{faster-whisper,
  title={Faster Whisper transcription with CTranslate2},
  author={Systran},
  year={2023},
  howpublished={\url{https://github.com/SYSTRAN/faster-whisper}}
}
```

**License**: MIT  
**Repository**: https://github.com/SYSTRAN/faster-whisper  
**Usage**: Optimized Whisper inference engine

---

### 6. PyTorch - Deep Learning Framework
**Citation**:
```bibtex
@incollection{pytorch2019,
  title={PyTorch: An Imperative Style, High-Performance Deep Learning Library},
  author={Paszke, Adam and Gross, Sam and Massa, Francisco and Lerer, Adam and Bradbury, James and Chanan, Gregory and Killeen, Trevor and Lin, Zeming and Gimelshein, Natalia and Antiga, Luca and others},
  booktitle={Advances in Neural Information Processing Systems 32},
  year={2019}
}
```

**License**: BSD-3-Clause  
**Repository**: https://github.com/pytorch/pytorch  
**Usage**: Neural network backend for all models

---

### 7. MLX - Apple Silicon Acceleration
**Citation**:
```bibtex
@software{mlx2023,
  author = {Apple},
  title = {MLX: An Array Framework for Apple Silicon},
  year = {2023},
  url = {https://github.com/ml-explore/mlx}
}
```

**License**: MIT  
**Repository**: https://github.com/ml-explore/mlx  
**Usage**: Hardware acceleration on M1/M2/M3 chips

---

### 8. Hugging Face Transformers
**Citation**:
```bibtex
@inproceedings{wolf2020transformers,
  title={Transformers: State-of-the-art natural language processing},
  author={Wolf, Thomas and Debut, Lysandre and Sanh, Victor and Chaumond, Julien and Delangue, Clement and Moi, Anthony and Cistac, Pierric and Rault, Tim and Louf, Rémi and Funtowicz, Morgan and others},
  booktitle={Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations},
  year={2020}
}
```

**License**: Apache 2.0  
**Repository**: https://github.com/huggingface/transformers  
**Usage**: Model loading and inference infrastructure

---

## Hugging Face Model Usage

### IndicTrans2 Models
```python
# Model: ai4bharat/indictrans2-en-indic-1B
# License: MIT
# Auto-downloaded via transformers.AutoModelForSeq2SeqLM

# Model: ai4bharat/indictrans2-indic-indic-1B  
# License: MIT
# Auto-downloaded via transformers.AutoModelForSeq2SeqLM
```

### NLLB Model
```python
# Model: facebook/nllb-200-distilled-600M
# License: CC-BY-NC 4.0 (Non-commercial use)
# Auto-downloaded via transformers.AutoModelForSeq2SeqLM
```

**Note**: First run downloads models from Hugging Face Hub to `~/.cache/huggingface/`. Requires internet connection.

---

## License Compliance

### CP-WhisperX-App License
- **License**: MIT
- **Copyright**: 2024 CP-WhisperX-App Contributors
- **Commercial Use**: Allowed for components under MIT/Apache/BSD licenses
- **NLLB Restriction**: CC-BY-NC 4.0 limits commercial use of NLLB translations

### Component License Summary

| Component | License | Commercial Use | Attribution Required |
|-----------|---------|----------------|---------------------|
| WhisperX | BSD-4-Clause | ✅ Yes | ✅ Yes |
| Whisper (OpenAI) | MIT | ✅ Yes | ✅ Yes |
| IndicTrans2 | MIT | ✅ Yes | ✅ Yes |
| **NLLB-200** | **CC-BY-NC 4.0** | **❌ No** | **✅ Yes** |
| Faster-Whisper | MIT | ✅ Yes | ✅ Yes |
| PyTorch | BSD-3-Clause | ✅ Yes | ✅ Yes |
| MLX | MIT | ✅ Yes | ✅ Yes |
| Transformers | Apache 2.0 | ✅ Yes | ✅ Yes |

⚠️ **Important**: NLLB-200 is licensed under CC-BY-NC 4.0, which prohibits **commercial use**. If using this pipeline for commercial purposes, avoid using NLLB translations or obtain appropriate licensing.

---

## External Services

### FFmpeg
**License**: LGPL 2.1+ or GPL 2+ (depending on build configuration)  
**Usage**: Audio/video processing (demux, mux, format conversion)  
**Repository**: https://github.com/FFmpeg/FFmpeg  
**Note**: Binary must be installed separately

---

## Data Privacy

### Hugging Face Hub
- Models downloaded from https://huggingface.co
- No data transmitted to Hugging Face during inference
- Models cached locally after first download
- Optional: Set `HF_HUB_OFFLINE=1` to prevent online checks

### No External API Calls
- All processing runs locally
- No transcripts or translations sent to external services
- Complete data privacy and GDPR compliance

---

## Acknowledgments

Special thanks to:
- **Max Bain** and team for WhisperX
- **OpenAI** for Whisper foundation models
- **AI4Bharat** for IndicTrans2 Indic language support
- **Meta AI** for NLLB-200 universal translation
- **Systran** for Faster-Whisper optimization
- **Apple** for MLX framework
- **Hugging Face** for model distribution infrastructure

---

## How to Cite This Project

If you use CP-WhisperX-App in your research or project, please cite the underlying technologies and this pipeline:

```bibtex
@software{cp_whisperx_app,
  title={CP-WhisperX-App: Multi-Environment ASR, Translation & Subtitle Pipeline},
  author={CP-WhisperX-App Contributors},
  year={2024},
  url={https://github.com/yourorg/cp-whisperx-app},
  note={Combines WhisperX, IndicTrans2, and NLLB-200 for multilingual subtitle generation}
}
```

---

**Last Updated**: November 20, 2025  
**Version**: 2.0.0
