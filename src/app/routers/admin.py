import uuid
import os

from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, Request, UploadFile, File
from sqlmodel import Session, select

from app.worker import celery_app

from app.database import get_db
from app.models.document import Document
from app.models.user import User

from app.schemas.admin import FileStatus, DocumentResponse, DeleteRequest
from app.schemas.common import APIResponse

from app.security.permissions import RequireRole
from app.security.dependencies import GetUser

from app.tasks import embed_document

router = APIRouter(prefix="/v1/admin", tags=["Admin"], dependencies=[Depends(RequireRole("admin"))])


@router.post("/insertdoc", response_model=APIResponse[FileStatus], status_code=201)
def insert_document(
    file: UploadFile = File(), 
    user: User = Depends(GetUser()), 
    session: Session = Depends(get_db),
):
    
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    base_dir = Path("src/docs")
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

    embed_document.delay(document.id, str(file_path))

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

    results = session.exec(select(Document, User).join(User, isouter=True).order_by(
        Document.filename.desc() if descending else Document.filename.asc()
    ).offset(offset).limit(limit)).all()
    return APIResponse(
        status_code=200, 
        message="Document returned successfully", 
        data={
            "document_items": [
                {"document_id": document.id, "document_name": document.filename, "document_status": document.status, "time_upload": document.created_at, "user": user.username}
                for document, user in results
            ]
        })