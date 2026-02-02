from app.config import get_settings
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

import os
from pathlib import Path


if __name__ == "__main__":
    settings = get_settings()

    TextEmbedding(model_name=settings.EMBEDDING_MODEL, cache_dir="/models/huggingface")
    TextCrossEncoder(model_name=settings.RERANK_MODEL, cache_dir="/models/huggingface")