from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

from typing import Union, List, Literal
from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy import text, bindparam, func

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
            rank_type: Literal["semantic", "lexical"] = "semantic",
            embedding_model: str = settings.EMBEDDING_MODEL,
    ):
        self.k = k
        self.k_fetch = int(k * 1.5)
        self.rank_type = rank_type
        self.embed_model = TextEmbedding(model_name=embedding_model, cache_dir="/models/huggingface")

    def retrieve(self, session: Session, query: str) -> List[str]:
        if self.rank_type == "semantic":
            with timer("semantic_retrieve"):
                documents = self._semantic_retrieve(session, query, self.k)
        else:
            with timer("lexical_retrieve"):
                documents = self._lexical_retrieve(session, query, self.k)

        documents_contents = [document[1] for document in documents]
        return documents_contents

    def _semantic_retrieve(self, session: Session, query: str, k: int):
        embed_query = list(self.embed_model.query_embed(query))[0]

        documents = session.exec(
            select(DocumentVector.id, DocumentVector.content, DocumentVector.dense_embedding).order_by(DocumentVector.dense_embedding.cosine_distance(embed_query)).limit(self.k_fetch)
        ).all()

        document_embeddings = np.array([document[2] for document in documents])
        mmr_selected = self._mmr(np.array(embed_query), document_embeddings, k)

        documents = [documents[i] for i in mmr_selected]
        documents = [(document[0], document[1]) for document in documents]

        return documents
    
    def _lexical_retrieve(self, session: Session, query: str, k: int):
        statement = text(f"SELECT id, content, content <@> to_bm25query('{query}', 'docs_idx') as score FROM document_vectors ORDER BY score LIMIT {k};")
        # statement = text(f"SELECT id, content FROM document_vectors ORDER BY content <@> '{query}' LIMIT {k};")

        documents = session.exec(statement=statement)
        documents = [(document[0], document[1]) for document in documents]

        return documents
    

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


class HybridRetriever(BaseRetriever):
    def __init__(
            self,
            k: int = 50,
            k_rrf: int = 5, 
            rank_type: Literal["semantic", "lexical"] = "semantic",
            embedding_model: str = settings.EMBEDDING_MODEL
    ):
        super().__init__(k, rank_type, embedding_model)
        self.k_rrf = k_rrf

    
    def retrieve(self, session: Session, query: str):
        with timer("semantic_retrieve"):
            semantic_documents = self._semantic_retrieve(session, query, self.k)
        with timer("lexical_retrieve"):
            lexical_documents = self._lexical_retrieve(session, query, self.k)
        with timer("rrf"):
            documents_contents = self._rrf(session, semantic_documents, lexical_documents)

        return documents_contents
    
    def _rrf(self, session: Session, *document_rankings, k = 60):
        document_score = {}
        for document_ranking in document_rankings:
            for i, document in enumerate(document_ranking):
                rank = i + 1
                document_id = document[0]
                score = 1 / (k + rank)
                document_score[document_id] = (
                    document_score.get(document_id, 0.0) + score
                )

        document_final_score = sorted(
            document_score.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.k_rrf]

        document_final_score = [document[0] for document in document_final_score]

        documents = session.exec(select(DocumentVector.content).where(DocumentVector.id.in_(document_final_score))).all()

        return documents
    

class RerankRetriever(BaseRetriever):
    def __init__(
            self, 
            k = 50, 
            k_rerank = 5,
            rank_type = "semantic", 
            embedding_model = settings.EMBEDDING_MODEL, 
            rerank_model = settings.RERANK_MODEL
    ):
        super().__init__(k, rank_type, embedding_model)
        
        self.k_rerank = k_rerank
        self.reranker = TextCrossEncoder(model_name=rerank_model, cache_dir="/models/huggingface")

    def retrieve(self, session: Session, query: str):
        document_contents = super().retrieve(session, query)
        with timer("rerank"):
            document_contents = self._rerank(query, document_contents)

        return document_contents

    def _rerank(self, query: str, document_contents: List[str]):
        new_scores = self.reranker.rerank(query, document_contents)
        ranking = [(i, score) for i, score in enumerate(new_scores)]
        ranking.sort(key=lambda x: x[1], reverse=True)

        return [document_contents[i] for i, score in ranking[:self.k_rerank]]