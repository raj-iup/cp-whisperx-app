# Citations and References

This project builds upon several open-source projects and research works. Please cite the following if you use this work:

## IndicTrans2

The Hindi→English translation feature uses **IndicTrans2** by AI4Bharat:

```bibtex
@article{gala2023indictrans,
  title={IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22 Scheduled Indian Languages},
  author={Jay Gala and Pranjal A Chitale and A K Raghavan and Varun Gumma and Sumanth Doddapaneni and Aswanth Kumar M and Janki Atul Nawale and Anupama Sujatha and Ratish Puduppully and Vivek Raghavan and Pratyush Kumar and Mitesh M Khapra and Raj Dabre and Anoop Kunchukuttan},
  journal={Transactions on Machine Learning Research},
  issn={2835-8856},
  year={2023},
  url={https://openreview.net/forum?id=vfT4YuzAYA},
  note={}
}
```

**Paper**: [IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22 Scheduled Indian Languages](https://openreview.net/forum?id=vfT4YuzAYA)  
**Model**: [ai4bharat/indictrans2-indic-en-1B](https://huggingface.co/ai4bharat/indictrans2-indic-en-1B)  
**GitHub**: [AI4Bharat/IndicTrans2](https://github.com/AI4Bharat/IndicTrans2)

### IndicTrans2 Model Card

- **Model Name**: ai4bharat/indictrans2-indic-en-1B
- **Model Type**: Sequence-to-sequence translation model
- **Languages**: 22 Scheduled Indian Languages → English
- **Parameters**: 1.1 billion
- **License**: See [HuggingFace Model Card](https://huggingface.co/ai4bharat/indictrans2-indic-en-1B)
- **Intended Use**: High-quality translation from Indian languages to English
- **Training Data**: See Appendix D of the IndicTrans2 paper

## WhisperX

Automatic speech recognition and alignment:

```bibtex
@article{bain2022whisperx,
  title={WhisperX: Time-Accurate Speech Transcription of Long-Form Audio},
  author={Bain, Max and Huh, Jaesung and Han, Tengda and Zisserman, Andrew},
  journal={arXiv preprint arXiv:2303.00747},
  year={2023}
}
```

**Paper**: [WhisperX: Time-Accurate Speech Transcription of Long-Form Audio](https://arxiv.org/abs/2303.00747)  
**GitHub**: [m-bain/whisperX](https://github.com/m-bain/whisperX)

## OpenAI Whisper

Speech recognition model:

```bibtex
@article{radford2022robust,
  title={Robust speech recognition via large-scale weak supervision},
  author={Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya},
  journal={arXiv preprint arXiv:2212.04356},
  year={2022}
}
```

**Paper**: [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356)  
**GitHub**: [openai/whisper](https://github.com/openai/whisper)

## PyAnnote Audio

Speaker diarization:

```bibtex
@inproceedings{bredin2020pyannote,
  title={pyannote.audio: neural building blocks for speaker diarization},
  author={Bredin, Hervé and Yin, Ruiqing and Coria, Juan Manuel and Gelly, Gregory and Korshunov, Pavel and Lavechin, Marvin and Fustes, Diego and Titeux, Hadrien and Bouaziz, Wassim and Gill, Marie-Philippe},
  booktitle={ICASSP 2020-2020 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)},
  pages={7124--7128},
  year={2020},
  organization={IEEE}
}
```

**GitHub**: [pyannote/pyannote-audio](https://github.com/pyannote/pyannote-audio)

## HuggingFace Transformers

```bibtex
@inproceedings{wolf2020transformers,
  title={Transformers: State-of-the-art natural language processing},
  author={Wolf, Thomas and Debut, Lysandre and Sanh, Victor and Chaumond, Julien and Delangue, Clement and Moi, Anthony and Cistac, Pierric and Rault, Tim and Louf, Rémi and Funtowicz, Morgan and others},
  booktitle={Proceedings of the 2020 conference on empirical methods in natural language processing: system demonstrations},
  pages={38--45},
  year={2020}
}
```

**GitHub**: [huggingface/transformers](https://github.com/huggingface/transformers)

## Contributing

If you use this project in your research or production systems, please consider:

1. Citing the relevant papers above
2. Acknowledging the AI4Bharat team for IndicTrans2
3. Linking back to this repository
4. Reporting issues and contributing improvements

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Individual components (IndicTrans2, WhisperX, etc.) are subject to their own licenses. Please check their respective repositories for license information.

## Acknowledgments

Special thanks to:

- **AI4Bharat** for developing and open-sourcing IndicTrans2
- **Max Bain et al.** for WhisperX
- **OpenAI** for Whisper
- **HuggingFace** for the Transformers library
- **PyAnnote** team for speaker diarization tools
- All contributors to the open-source NLP and speech processing communities

---

*For questions about citations or licensing, please open an issue in the repository.*
