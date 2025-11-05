Awesome — I dug through your repo (zip) and the Dockerfiles. Here’s a tight diagnosis and a step-by-step improvement plan to cut both build time and image size, with concrete snippets you can drop in.

---

# What you have (quick read)

* **Layered base images**: `base` → `base-cuda` → `base-ml`; stages (e.g., `asr`, `diarization`, `vad`, `mux`) `FROM` the base images. Good foundation for caching and DRY.
* **GPU stack**: `nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04` in `base-cuda`; `base-ml` installs PyTorch & common ML libs; stage images add small extras (e.g., WhisperX, pyannote). Good separation.
* **Reasonable Python env**: `python:3.11-slim` for CPU base; `PYTHONDONTWRITEBYTECODE=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1`. You’re also using shared `requirements-common.txt` (nice).
* **Copy order**: generally copying requirements before app code to leverage cache (👍).

### Key opportunities

1. **Build cache is throttled**: global `PIP_NO_CACHE_DIR=1` nukes pip’s cache layers (slower rebuilds).
2. **BuildKit cache mounts not used**: no `--mount=type=cache` for pip/apt → repeated downloads/installs.
3. **Apt layers could be slimmer**: missing `--no-install-recommends` and cleanup in same `RUN`.
4. **Wheel-building & native deps**: heavy libs (e.g., librosa, pyannote deps) recompile often; a wheelhouse stage will speed things up and shrink final images.
5. **Base image pinning**: CUDA image not pinned by digest → cache invalidations.
6. **.dockerignore**: not visible; likely room to exclude build junk, models, caches.
7. **Models & HF cache**: bakes into image or redownloads per stage; better handled via a shared runtime volume.
8. **Multi-arch / buildx cache**: not enabled with `--cache-from/--cache-to`, so CI builds redo work.

---

# High-impact, low-risk changes (do first)

## 1) Turn on BuildKit + pip/apt cache mounts

**Why**: Reuses downloaded wheels and apt lists across builds; massive speedup with zero runtime bloat.

At build time:

```bash
DOCKER_BUILDKIT=1 docker buildx build \
  --cache-to=type=inline \
  --cache-from=type=registry,ref=YOUR_REGISTRY/your-image:cache \
  -t YOUR_IMAGE:tag .
```

In Dockerfiles (example `base-cuda` & `base-ml`):

```dockerfile
# Enable BuildKit inline cache (no code change required; just build flags)

# APT with cache mount
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates curl python3-pip git ffmpeg tini \
      # + only what you actually need
    && rm -rf /var/lib/apt/lists/*

# PIP with cache mount (drop global PIP_NO_CACHE_DIR here)
# Keep your ENV but override for the line using cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-common.txt
```

> Tip: keep `PIP_NO_CACHE_DIR=1` globally if you like, but for the **install** lines use a cache mount so pip can reuse downloads.

## 2) Split & lock requirements; install in the right order

**Why**: Stable layers that rarely change stay cached.

Suggested files:

* `requirements-common.txt` (already present) – keep stable, widely shared.
* `requirements-ml.txt` – torch/torchaudio/torchvision (CUDA-correct), HF stack.
* `requirements-stage.txt` per stage (tiny deltas).

Install order in `base-ml`:

```dockerfile
COPY requirements-common.txt /tmp/
COPY requirements-ml.txt /tmp/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-common.txt -r /tmp/requirements-ml.txt
```

Then in each stage:

```dockerfile
COPY docker/<stage>/requirements.txt /tmp/requirements-stage.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-stage.txt
```

Add hashes if you can:

```txt
# requirements-ml.txt
torch==2.1.0 --hash=sha256:... 
# etc
```

## 3) Wheelhouse builder (multi-stage)

**Why**: Build native wheels once; copy only wheels → smaller, faster final images.

```dockerfile
# Stage 1: wheels
FROM python:3.11-slim AS wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /wheels \
      -r /tmp/requirements-common.txt \
      -r /tmp/requirements-ml.txt

# Stage 2: runtime (CUDA or slim base)
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
COPY --from=wheels /wheels /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=/wheels \
      -r /tmp/requirements-common.txt \
      -r /tmp/requirements-ml.txt \
  && rm -rf /wheels
```

For CPU images, swap CUDA base for `python:3.11-slim`.

## 4) APT hygiene and minimalism

**Why**: Smaller layers, fewer cache busts.

* Always use `--no-install-recommends`.
* Install and clean in **one** `RUN`.
* Avoid `apt-get upgrade`.
* Only include build tools (`build-essential`, `ffmpeg-dev`, etc.) in the **builder** stage; not runtime.

## 5) Pin base images by digest

**Why**: Reproducible builds and better cache hit rate.

```dockerfile
FROM nvidia/cuda@sha256:<digest-for-12.1.0-cudnn8-runtime-ubuntu22.04>
```

(Keep tag comment next to it for humans.)

## 6) .dockerignore

**Why**: Prevents accidental cache busts and large contexts.

`.dockerignore` (starter):

```
.git
**/__pycache__/
*.pyc
*.pyo
*.pyd
.env
*.log
dist/
build/
.wheels/
.cache/
data/
models/
checkpoints/
notebooks/
**/.DS_Store
```

---

# Medium effort wins

## 7) Shared model cache via volume (don’t bake into images)

**Why**: Smaller images; faster cold starts after first run.

Use a named volume for HuggingFace & Whisper caches across all services:

```yaml
# docker-compose.yml
volumes:
  hf-cache:

services:
  asr:
    volumes:
      - hf-cache:/home/appuser/.cache/huggingface
      - hf-cache:/home/appuser/.cache/whisper
```

Set at runtime:

```bash
HF_HOME=/home/appuser/.cache/huggingface
TRANSFORMERS_CACHE=$HF_HOME/transformers
```

Optionally, add a tiny init step to pre-pull specific models into the volume (not the image).

## 8) Use `ENTRYPOINT ["tini","--"]` as PID 1

**Why**: Proper signal handling; no size impact; often already present via apt.

```dockerfile
ENTRYPOINT ["tini", "--", "python", "/app/whisperx_asr.py"]
```

## 9) Reduce Python footprint appropriately

You already set `PYTHONDONTWRITEBYTECODE=1` (keeps images slimmer). Keep it.
If startup perf matters, you can **compile** only the app code to pyc in a single layer and keep libs uncompiled:

```dockerfile
RUN python -m compileall -q /app
```

(This adds a bit of size; optional.)

## 10) Consolidate small `RUN` steps

Where you have sequences of small installs/copies, combine logically to reduce layers (but don’t over-combine unrelated steps that would bust cache too often).

---

# CI / build graph speedups

## 11) Use buildx with registry cache

* **Push inline cache** from CI:

  ```bash
  docker buildx build \
    --cache-to=type=registry,mode=max,ref=$REGISTRY/$IMAGE:buildcache \
    --cache-from=type=registry,ref=$REGISTRY/$IMAGE:buildcache \
    -t $REGISTRY/$IMAGE:$TAG .
  ```
* Build **base** images first (`base`, `base-cuda`, `base-ml`), then parallelize the small stage images (they’ll reuse cached layers).

## 12) Parameterize CPU/GPU targets

Keep one Dockerfile per logical layer, but allow:

```bash
docker buildx build --target cpu -f base/Dockerfile .
docker buildx build --target cuda -f base-cuda/Dockerfile .
```

Or two files, but same ARGs/labels to keep tags consistent.

---

# Example refactors (drop-in)

## A. `base-cuda` (excerpt)

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps (minimal, no recommends), cached
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv \
      ca-certificates curl git ffmpeg tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Shared requirements installed with pip cache
COPY requirements-common.txt /tmp/requirements-common.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements-common.txt && \
    rm -f /tmp/requirements-common.txt

# Non-root user
RUN useradd -m -u 1000 appuser && mkdir -p /app/{in,out,logs,temp,config,shared} \
    && chown -R appuser:appuser /app
USER appuser
ENV PYTHONPATH=/app:/app/shared
```

## B. `base-ml` (excerpt)

```dockerfile
ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cuda

USER root
WORKDIR /app

COPY requirements-ml.txt /tmp/requirements-ml.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-ml.txt \
 && python - <<'PY'
import torch; print("Torch:", torch.__version__)
PY

USER appuser
```

## C. `asr` (excerpt)

```dockerfile
ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base-ml:cuda

USER root
WORKDIR /app

COPY docker/asr/requirements.txt /tmp/requirements-asr.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-asr.txt

# Copy shared modules first (less frequent change)
COPY shared/ /app/shared/
COPY scripts/ /app/scripts/

# Copy the frequently changing app code last for cache efficiency
COPY docker/asr/whisperx_asr.py /app/

USER appuser
ENTRYPOINT ["tini","--","python","/app/whisperx_asr.py"]
```

`docker/asr/requirements.txt` should contain only stage-specific extras (e.g., `whisperx`, `ctranslate2`, etc.), keeping base images pristine.

---

# Optional size-focused extras

* **Strip docs/locales** in Ubuntu (minor wins, advanced):

  ```dockerfile
  RUN rm -rf /usr/share/{doc,man,locale}/* /var/cache/*
  ```
* **Distroless Python** for CPU-only micro-services (not CUDA): move to `gcr.io/distroless/python3` and copy site-packages + minimal runtime files. (Great size drop, but keep for simple services like `tmdb`.)
* **Static ffmpeg** for `demux`: copy only the `ffmpeg` binary (no dev libs) if you currently install the full package.

---

# Rollout order (safe & practical)

1. **Enable BuildKit & cache mounts** (pip/apt) across all Dockerfiles.
2. **Split requirements** and adjust install order.
3. **Introduce wheelhouse builder** for `base-ml`.
4. **Add .dockerignore**.
5. **Pin base images by digest**.
6. **Adopt buildx cache in CI** and build base images first.
7. **Add shared model cache volume** (compose) and stop baking models into images. Utilize shared-model-and-cache/ directory.
8. (Optional) Distroless for simple CPU services.

---
