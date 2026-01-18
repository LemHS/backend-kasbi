from typing import Sequence, Any, List
from uuid import uuid4

from docling.document_converter import DocumentConverter
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


class ChromaVectorDatabase():
    def __init__(
            self, 
            persist_directory:str,
            model_name:str = "BAAI/bge-m3",
            split_text:bool = True,
            chunk_size:int = 900,
            chunk_overlap:int = 100,
    ):
        self.persist_directory = persist_directory
        self.embed_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={
                "device": "cuda"
            },
            encode_kwargs={
                "batch_size": 32,
                "normalize_embeddings": True,
            },
        )
        self.split_text = split_text

        if split_text:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ).from_tiktoken_encoder()

        self.vector_db = Chroma(
            collection_name="documents",
            embedding_function=self.embed_model,
            persist_directory=persist_directory,
        )

    def insert_documents(self, file_paths: Sequence[str]) -> List[Document]:
        if getattr(self, "converter", None) is None:
            self._init_converter()

        documents = self.converter.convert_all(file_paths)
        documents = [Document(page_content=doc.document.export_to_text(), metadata={"path":path}) for doc, path in zip(documents, file_paths)]
        
        split_documents = self.text_splitter.split_documents(documents)

        uuids = [str(uuid4()) for i in range(len(split_documents))]
        self.vector_db.add_documents(split_documents, ids=uuids)

        return documents
    
    def get_retriever(self, k: int, fetch_k: int, lambda_mult: int):
        return self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult,
            }
        )
    
    def _init_converter(self) -> None:
        accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.CUDA,
        )

        pipeline_options = ThreadedPdfPipelineOptions(
            ocr_batch_size=64,   
            layout_batch_size=64,
            table_batch_size=4,
        )

        self.converter = DocumentConverter(
            format_options={
                "accelerator_options": accelerator_options,
                "pipeline_options": pipeline_options
            }
        )