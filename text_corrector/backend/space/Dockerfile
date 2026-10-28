# syntax=docker/dockerfile:1
# ──────────────────────────────────────────────────────────────────────────────
# Hugging Face SPACE image — the same serving stack as ../Dockerfile.serve, but
# the trained detector and the corrector lexicon are downloaded from the model
# repo at a pinned revision instead of being copied from local files, so the
# Space repo holds only code. Uploaded as the Space's Dockerfile by
# scripts/deploy_space.py; after scripts/publish_model.py, set MODEL_REVISION
# to the commit it prints.
# ──────────────────────────────────────────────────────────────────────────────

# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-serve.txt .

# torch==2.12.1+cpu resolves only from the PyTorch CPU index (see Dockerfile.serve)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements-serve.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.13-slim
WORKDIR /app

# libgomp1: CPU torch needs OpenMP at import (else silent PlaceholderModel)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/tmp/hf \
    KAZAKH_MODEL_PATH=/app/models/kazakh_detector

COPY --from=builder /install /usr/local

# Model + lexicon from the model repo (huggingface_hub comes with transformers).
# Pinned so a rebuild never picks up an untested model.
ARG MODEL_REPO=daniyar51/kazroberta-kazakh-spelling-detector
ARG MODEL_REVISION=d0459c3fe71df0c6fb07587f1a5351aac049f795
RUN python -c "from huggingface_hub import snapshot_download; \
snapshot_download('${MODEL_REPO}', revision='${MODEL_REVISION}', \
local_dir='/app/models/kazakh_detector', \
allow_patterns=['config.json', 'tokenizer.json', 'tokenizer_config.json', \
'model.safetensors', 'kk_lexicon.tsv'])" && \
    mkdir -p /app/data && \
    mv /app/models/kazakh_detector/kk_lexicon.tsv /app/data/kk_lexicon.tsv && \
    rm -rf /app/models/kazakh_detector/.cache

# From here on the app never touches the network
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY app/ ./app/

# UID 1000 is the user Hugging Face Spaces run containers as
RUN useradd --uid 1000 --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request,json,sys; d=json.load(urllib.request.urlopen('http://localhost:8000/health',timeout=5)); x=d['details']; sys.exit(0 if x.get('kazakh_model_ready')=='True' and 'TransformerModel' in x.get('kazakh_model','') else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
