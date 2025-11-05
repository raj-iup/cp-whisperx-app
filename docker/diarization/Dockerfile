# Diarization container - Speaker labeling using PyAnnote
ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base-ml:cuda

LABEL description="PyAnnote Diarization - Speaker labeling (MANDATORY per workflow-arch.txt)"

USER root

# FFmpeg and its libraries are already installed in base-ml:cuda
# PyTorch, numpy, transformers, librosa also available from base-ml:cuda
# Install PyAnnote and dependencies
RUN pip install --no-cache-dir \
    av \
    pyannote.audio==3.4.0 \
    pyannote.core==5.0.0 \
    pyannote.pipeline==3.0.1 \
    pytorch-lightning==2.5.5 \
    torchmetrics==1.8.2

# Install speechbrain separately
RUN pip install --no-cache-dir --no-build-isolation speechbrain==1.0.1

# Install whisperx for integration
RUN pip install --no-cache-dir whisperx==3.7.2

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/
COPY scripts/ /app/scripts/

# Copy stage script (changes most frequently)
COPY docker/diarization/diarization.py /app/

USER appuser
WORKDIR /app

# Set HuggingFace cache directory
ENV HF_HOME=/app/.cache/huggingface
ENV HF_DATASETS_CACHE=/app/.cache/huggingface/datasets
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers

ENTRYPOINT ["python", "/app/diarization.py"]
