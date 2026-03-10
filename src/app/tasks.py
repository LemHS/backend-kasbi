# app/tasks.py
from pathlib import Path
from app.worker import celery_app
from app.database import SessionLocal
from app.models.document import Document
from app.agents import instansiate_vector_db
from celery import Task
from celery.exceptions import WorkerLostError


class EmbedDocumentTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        document_id = args[0]
        self._mark_failed(document_id)

    def on_success(self, retval, task_id, args, kwargs):
        pass  # status is set inside the task itself

    def _mark_failed(self, document_id):
        session = SessionLocal()
        try:
            document = session.get(Document, document_id)
            if document:
                document.status = "failed"
                session.commit()
        finally:
            session.close()


@celery_app.task(
    base=EmbedDocumentTask,
    name="embed_document",
    acks_late=True,  # ensures WorkerLostError is detectable
    reject_on_worker_lost=False,  # don't requeue — just fail
)
def embed_document(document_id, file_path):
    """Background task to embed a document into the vector database."""
    session = SessionLocal()
    try:
        vector_db = instansiate_vector_db()
        vector_db.insert_documents(session, [Path(file_path)], document_ids=[document_id])

        document = session.get(Document, document_id)
        if document is None:
            return

        document.status = "done"
        session.commit()
    finally:
        session.close()