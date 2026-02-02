import uuid
import os

from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, Request, UploadFile, File
from sqlmodel import Session, select

# from app.worker import celery_app

from app.database import get_db
from app.models.document import Document
from app.models.user import User

from app.schemas.admin import FileStatus, DocumentResponse, DeleteRequest
from app.schemas.common import APIResponse

from app.security.permissions import RequireRole
from app.security.dependencies import GetUser

# @celery_app.task(name="embed_document")
def _embed_document(document_id, file_path):
    from app.database import SessionLocal
    from app.models.document import Document
    from app.agents import instansiate_vector_db

    session = SessionLocal()

    try:
        vector_db = instansiate_vector_db()
        vector_db.insert_documents(session, [Path(file_path)], document_ids=[document_id])

        document = session.get(Document, document_id)
        document.status = "done"

        session.commit()
    finally:
        session.close()



router = APIRouter(prefix="/v1/admin", tags=["Admin"], dependencies=[Depends(RequireRole("admin"))])


@router.post("/insertdoc", response_model=APIResponse[FileStatus], status_code=201)
def insert_document(
    file: UploadFile = File(), 
    user: User = Depends(GetUser()), 
    session: Session = Depends(get_db),
):
    
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    base_dir = Path("docs")
    base_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / safe_name

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    document = Document(
        filename=safe_name,
        filepath=str(file_path),
        user_id=user.id,
        status="pending"
    )

    session.add(document)
    session.commit()

    _embed_document(document.id, str(file_path))

    return APIResponse(status_code=201, message="Insert pending", data={"status": "pending"})

@router.delete("/deldoc", response_model=APIResponse)
def del_documents(
    payload: DeleteRequest,
    session: Session = Depends(get_db)
) -> APIResponse:

    documents = session.exec(
        select(Document).where(Document.id == payload.document_id)
    ).one()

    session.delete(documents)
    session.commit()

    return APIResponse(
        status_code=200, 
        message="Document deleted successfully")


@router.get("/documents", response_model=APIResponse[DocumentResponse])
def get_documents(
    session: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 10,
    descending: bool = True,
) -> APIResponse[DocumentResponse]:

    documents = session.exec(select(Document).order_by(
        Document.filename.desc() if descending else Document.filename.asc()
    ).offset(offset).limit(limit)).all()
    return APIResponse(
        status_code=200, 
        message="Document returned successfully", 
        data={
            "documents": [
                {"document_id": document.id, "document_name": document.filename}
                for document in documents
            ]
        })