from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.documents import Document

from typing import Union, List
from pathlib import Path

from agents.database import ChromaVectorDatabase

from config import get_settings

settings = get_settings()

class BaseRetriever():
    def __init__(
            self,
            k: int = 50,
            k_rerank: int = 15,
            db_directory: Path = settings.VECTOR_DB_DIRECTORY,
            embedding_model: str = settings.EMBEDDING_MODEL,
            rerank_model: str = settings.RERANK_MODEL
    ):
        self.vector_db = ChromaVectorDatabase(
            persist_directory=db_directory,
            model_name=embedding_model
        )

        self.compressor = FlashrankRerank(top_n=k_rerank)
        
        self.retriever = self.vector_db.get_retriever(k=k, fetch_k=int(k*1.5), lambda_mult=0.7)

        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor, base_retriever=self.retriever
        )

    def semantic_retrieve(self, query: str, rerank: bool) -> Document:
        if rerank:
            result = self.compression_retriever.invoke(query)
        else:
            result = self.retriever.invoke(query)

        return self._extract_page_content(result)
    
    def _extract_page_content(
        self, result: Union[List[Document], Document]
    ) -> List[str]:
        if isinstance(result, list):
            return [doc.page_content for doc in result]
        return [result.page_content]