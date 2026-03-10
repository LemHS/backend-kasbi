from typing import Sequence, Any, List
from uuid import uuid4
from pathlib import Path
import gc

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
            batch_size: int = 4,  # Added batch size parameter
            max_workers: int = 1,  # Limit concurrent processing
    ):
        # Initialize embedding model lazily to save memory
        self.model_name = model_name
        self.embed_model = None
        self.split_text = split_text
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.converter = None  # Initialize lazily

        if split_text:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ).from_tiktoken_encoder()

    def _init_embed_model(self):
        """Lazy initialization of embedding model"""
        if self.embed_model is None:
            self.embed_model = TextEmbedding(
                model_name=self.model_name, 
                cache_dir="/models/huggingface",
                threads=self.max_workers  # Limit threads
            )

    def insert_documents(
            self, 
            session: Session, 
            file_paths: Sequence[str], 
            document_ids: Sequence[int]
        ) -> List[Document]:

        if self.converter is None:
            self._init_converter()

        documents = []

        # Process documents one at a time to reduce memory pressure
        for path, document_id in zip(file_paths, document_ids):
            try:  
                doc = self.converter.convert(path)
            except Exception as e:
                print(f"Error converting document {document_id}: {e}")
                document = session.exec(
                    select(Document).where(Document.id == document_id)
                ).one_or_none()

                if document:
                    session.delete(document)
                    session.commit()
            else:
                new_path = Path("converted_docs").joinpath(*Path(path).parts[-1:]).with_suffix(".md")
                new_path.parent.mkdir(parents=True, exist_ok=True)
                text_content = doc.document.export_to_markdown()

                with open(new_path, "w", encoding="utf-8") as f:
                    f.write(text_content)

                documents.append(Doc(page_content=text_content, metadata={"document_id": document_id}))
                
                # Clear the converted document from memory
                del doc
                gc.collect()
        
        # Split documents
        split_documents = self.text_splitter.split_documents(documents) if self.split_text else documents
        
        # Clear original documents from memory
        del documents
        gc.collect()

        # Initialize embedding model only when needed
        print("embedding documents")
        self._init_embed_model()

        # Process embeddings in batches to reduce memory usage
        for i in range(0, len(split_documents), self.batch_size):
            batch = split_documents[i:i + self.batch_size]
            
            for split_document in batch:
                document = session.exec(
                    select(Document).where(Document.id == split_document.metadata["document_id"])
                ).one_or_none()
                
                if not document:
                    continue
                
                try:
                    vector_embed = self.embed_document(split_document.page_content)
                    document_vector = DocumentVector(
                        dense_embedding=vector_embed,
                        content=split_document.page_content,
                        document_id=split_document.metadata["document_id"]
                    )
                    
                    document.status = "done"
                    session.add(document_vector)
                    session.add(document)
                    
                except Exception as e:
                    print(f"Error embedding document {document.id}: {e}")
                    document.status = "failed"
                    session.add(document)
            
            # Commit after each batch to prevent memory buildup
            session.commit()
            gc.collect()

        return split_documents
    
    def embed_document(self, page_content: str) -> List[float]:
        """Embed a single document with proper type handling"""
        if self.embed_model is None:
            self._init_embed_model()
            
        vector_embed = list(self.embed_model.embed([page_content]))
        return vector_embed[0].tolist() if hasattr(vector_embed[0], 'tolist') else list(vector_embed[0])
    
    def _init_converter(self) -> None:
        """Initialize document converter with CPU-optimized settings"""
        
        # CPU-optimized pipeline options
        pipeline_options = ThreadedPdfPipelineOptions(
            ocr_batch_size=1,      # Reduced from 64
            layout_batch_size=1,    # Reduced from 64
            table_batch_size=1,     # Reduced from 4
            queue_max_size=5,
        )

        self.converter = DocumentConverter(
            format_options={
                "pipeline_options": pipeline_options
            }
        )
    
    def cleanup(self):
        """Clean up resources to free memory"""
        if self.embed_model is not None:
            del self.embed_model
            self.embed_model = None
        if self.converter is not None:
            del self.converter
            self.converter = None
        gc.collect()