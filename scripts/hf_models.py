from app.config import get_settings
from transformers import AutoModel, AutoTokenizer
from flashrank import Ranker

import os
from pathlib import Path


if __name__ == "__main__":
    settings = get_settings()

    AutoModel.from_pretrained(settings.EMBEDDING_MODEL)
    AutoTokenizer.from_pretrained(settings.EMBEDDING_MODEL)

    Ranker(model_name=settings.RERANK_MODEL, cache_dir="/models/huggingface")
