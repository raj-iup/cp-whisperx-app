ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base-ml:cuda

LABEL description="PyAnnote VAD - Local voice activity detection with chunking"

USER root
WORKDIR /app

# PyTorch, numpy, soundfile, transformers, huggingface-hub already in base-ml
# Install pyannote.audio and dependencies
RUN pip install --no-cache-dir \
    pyannote.audio==3.4.0 \
    pyannote.core==5.0.0 \
    pytorch-lightning==2.5.5

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/

# Copy stage script (changes most frequently)
COPY docker/pyannote-vad/pyannote_vad.py /app/

USER appuser

# Set HuggingFace cache directory
ENV HF_HOME=/app/.cache/huggingface
ENV HF_DATASETS_CACHE=/app/.cache/huggingface/datasets
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers

ENTRYPOINT ["python", "pyannote_vad.py"]
