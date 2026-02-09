from typing import Sequence, Any, List
from uuid import uuid4
from pathlib import Path

from fastapi import Depends
from sqlmodel import Session, select

from docling.document_converter import DocumentConverter
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

from fastembed import TextEmbedding

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document as Doc

from app.database import get_db
from app.models.document import Document, DocumentVector


class VectorDatabase():
    def __init__(
            self,
            model_name: str = "BAAI/bge-m3",
            split_text: bool = True,
            chunk_size: int = 900,
            chunk_overlap: int = 100,
    ):
        self.embed_model = TextEmbedding(model_name=model_name, cache_dir="/models/huggingface")
        self.split_text = split_text

        if split_text:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ).from_tiktoken_encoder()

    def insert_documents(
            self, 
            session: Session, 
            file_paths: Sequence[str], 
            document_ids: Sequence[int]
        ) -> List[Document]:

        if getattr(self, "converter", None) is None:
            self._init_converter()

        documents = []

        for path, document_id in zip(file_paths, document_ids):
            try:  
                doc = self.converter.convert(path)
            except Exception as e:
                print(e)
                document = session.exec(
                    select(Document).where(Document.id == document_id)
                ).one()

                session.delete(document)
                session.commit()
            else:
                new_path = Path("converted_docs").joinpath(*Path(path).parts[-1:]).with_suffix(".md")
                new_path.parent.mkdir(parents=True, exist_ok=True)
                text_content = doc.document.export_to_markdown()

                with open(new_path, "w", encoding="utf-8") as f:
                    f.write(text_content)

                documents.append(Doc(page_content=text_content, metadata={"document_id": document_id}))
        
        split_documents = self.text_splitter.split_documents(documents)

        for split_document in split_documents:
            document = session.exec(
                    select(Document).where(Document.id == split_document.metadata["document_id"])
            ).one()
            try:
                vector_embed = self.embed_document(split_document.page_content)
                document_vector = DocumentVector(
                    dense_embedding=vector_embed,
                    content=split_document.page_content,
                    document_id=split_document.metadata["document_id"]
                )
            except Exception as e:
                print(e)
                document.status = "failed"

                session.add(document)
                session.commit()
            else:
                document.status = "done"

                session.add(document_vector)
                session.add(document)
                session.commit()

        return documents
    
    def embed_document(self, page_content: str) -> List[int]:
        vector_embed = list(self.embed_model.embed(page_content))

        return vector_embed[0]
    
    def _init_converter(self) -> None:
        # accelerator_options = AcceleratorOptions(
        #     device=AcceleratorDevice.CUDA,
        # )

        # pipeline_options = ThreadedPdfPipelineOptions(
        #     ocr_batch_size=64,   
        #     layout_batch_size=64,
        #     table_batch_size=4,
        # )

        self.converter = DocumentConverter(
            # format_options={
            #     "accelerator_options": accelerator_options,
            #     "pipeline_options": pipeline_options
            # }
        )