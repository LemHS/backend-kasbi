FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH" \
    UV_SYSTEM_PYTHON=1 \
    HF_HOME=/models/huggingface \
    TRANSFORMERS_CACHE=/models/huggingface

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

RUN useradd -m -u 1000 celeryuser

WORKDIR /backend

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --verbose

COPY . .

RUN chown -R celeryuser:celeryuser /backend

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY docker/celery_entrypoint.sh /celery_entrypoint.sh
RUN chmod +x /celery_entrypoint.sh

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
