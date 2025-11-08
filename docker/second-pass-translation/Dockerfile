ARG REGISTRY=rajiup
ARG BASE_TAG=cuda
FROM ${REGISTRY}/cp-whisperx-app-base-ml:${BASE_TAG}

LABEL description="Second Pass Translation - Refine translations with context"

USER root
WORKDIR /app

# PyTorch, transformers, sentencepiece already in base-ml
# Install additional translation dependencies if needed
RUN --mount=type=cache,id=pip-cache-second-pass,target=/root/.cache/pip \
    pip install protobuf==3.20.3

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/

# Copy stage script (changes most frequently)
COPY docker/second-pass-translation/second_pass_translation.py /app/

USER appuser

ENTRYPOINT ["python", "/app/second_pass_translation.py"]
