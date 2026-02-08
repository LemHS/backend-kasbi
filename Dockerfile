FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT=/backend/.venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /backend

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache \
    uv sync \
        --locked \
        --no-dev \
        --no-editable

RUN uv run pip uninstall -y opencv-python opencv-python-headless && \
    uv run pip install --no-cache-dir opencv-python-headless

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

ENV UV_SYSTEM_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT=/backend/.venv \
    HF_HOME=/models/huggingface \
    TRANSFORMERS_CACHE=/models/huggingface \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/

RUN useradd -m -u 1000 celeryuser

WORKDIR /backend

COPY --from=builder /backend/.venv /backend/.venv
COPY --from=builder /backend /backend

RUN mkdir -p /models/huggingface \
    && chown -R celeryuser:celeryuser /backend /models

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/celery_entrypoint.sh /celery_entrypoint.sh
RUN chmod +x /entrypoint.sh /celery_entrypoint.sh

EXPOSE 8000

# Use NVIDIA CUDA base image with Ubuntu
# FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# # Set environment variables
# ENV DEBIAN_FRONTEND=noninteractive \
#     PYTHONUNBUFFERED=1 \
#     CUDA_HOME=/usr/local/cuda \
#     PATH=/root/.local/bin:$PATH \
#     UV_SYSTEM_PYTHON=1

# # Install Python and system dependencies
# RUN apt-get update && apt-get install -y \
#     python3.11 \
#     python3.11-dev \
#     python3-pip \
#     curl \
#     git \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Create symbolic links for python
# RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
#     ln -sf /usr/bin/python3.11 /usr/bin/python3

# # Install uv
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# WORKDIR /backend

# COPY pyproject.toml uv.lock ./
# RUN uv sync --frozen --no-dev --verbose

# COPY . .

# COPY docker/entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

# EXPOSE 8000

# ENTRYPOINT ["/entrypoint.sh"]
