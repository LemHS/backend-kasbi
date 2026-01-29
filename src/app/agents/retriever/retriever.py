from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

from typing import Union, List
from pathlib import Path
from sqlmodel import Session, select

from app.models.document import Document, DocumentVector
from app.agents.database import VectorDatabase
from app.config import get_settings

import numpy as np
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"[TIMER] {name}: {(end - start)*1000:.2f} ms")


settings = get_settings()

class BaseRetriever():
    def __init__(
            self,
            k: int = 50,
            k_rerank: int = 15,
            embedding_model: str = settings.EMBEDDING_MODEL,
            rerank_model: str = settings.RERANK_MODEL
    ):
        self.k = k
        self.k_fetch = int(k * 1.5)
        self.k_rerank = k_rerank
        self.embed_model = TextEmbedding(model_name=embedding_model)
        self.reranker = TextCrossEncoder(model_name=rerank_model)

    def retrieve(self, session: Session, query: str, rerank: bool) -> List[str]:
        if rerank:
            with timer("total_retrieve"):
                with timer("semantic_retrieve"):
                    document_contents = self._semantic_retrieve(session, query, self.k)
                with timer("rerank"):
                    document_contents = self._rerank(query, document_contents)
        else:
            with timer("semantic_retrieve"):
                document_contents = self._semantic_retrieve(session, query, self.k_rerank)

        return document_contents

    def _semantic_retrieve(self, session: Session, query: str, k: int):
        embed_query = list(self.embed_model.query_embed(query))[0]

        documents = session.exec(
            select(DocumentVector.content, DocumentVector.embedding).order_by(DocumentVector.embedding.cosine_distance(embed_query)).limit(self.k_fetch)
        ).all()

        document_embeddings = np.array([document[1] for document in documents])
        mmr_selected = self._mmr(np.array(embed_query), document_embeddings, k)

        document_contents = [document[0] for document in documents]
        document_contents = [document_contents[i] for i in mmr_selected]

        return document_contents
        

    def _rerank(self, query: str, document_contents: List[str]):
        new_scores = self.reranker.rerank(query, document_contents)
        ranking = [(i, score) for i, score in enumerate(new_scores)]
        ranking.sort(key=lambda x: x[1], reverse=True)

        return [document_contents[i] for i, score in ranking[:self.k_rerank]]
    

    def _mmr(self, embed_query, doc_embeddings, k: int, lambda_mult: int = 0.5):
        selected = []
        candidates = list(range(len(doc_embeddings)))

        embed_query = embed_query / np.linalg.norm(embed_query)

        while len(selected) < k and candidates:
            mmr_scores = []

            for i in candidates:
                doc_emb = doc_embeddings[i]
                doc_emb = doc_emb / np.linalg.norm(doc_emb)

                sim_to_query = np.dot(doc_emb, embed_query)

                sim_to_selected = 0
                if selected:
                    sim_to_selected = max(
                        np.dot(doc_emb, doc_embeddings[j] / np.linalg.norm(doc_embeddings[j]))
                        for j in selected
                    )

                score = lambda_mult * sim_to_query - (1 - lambda_mult) * sim_to_selected
                mmr_scores.append((i, score))

            best = max(mmr_scores, key=lambda x: x[1])[0]
            selected.append(best)
            candidates.remove(best)

        return selected
