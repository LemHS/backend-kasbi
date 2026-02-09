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