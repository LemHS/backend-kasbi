# app/tasks.py
from pathlib import Path
from app.worker import celery_app
from app.database import SessionLocal
from app.models.document import Document
from app.agents import instansiate_vector_db

@celery_app.task(name="embed_document")
def embed_document(document_id, file_path):
    """Background task to embed a document into the vector database."""
    session = SessionLocal()
    try:
        import os

        if not os.path.exists(Path(file_path)):
            print("FILE NOT FOUND")

        print("File size:", os.path.getsize(Path(file_path)))

        with open(Path(file_path), "rb") as f:
            print("First bytes:", f.read(5))

        vector_db = instansiate_vector_db()
        vector_db.insert_documents(session, [Path(file_path)], document_ids=[document_id])
        
        document = session.get(Document, document_id)
        if document is None:
            session.close()
            return
        
        document.status = "done"
        session.commit()
    except Exception as e:
        print(e)
        document = session.get(Document, document_id)
        if document is None:
            session.close()
            return
        
        document.status = "failed"
        session.commit()
    finally:
        session.close()