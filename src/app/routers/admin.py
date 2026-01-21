import uuid
import os

from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from sqlmodel import Session

from app.database import get_db
from app.models.document import Document
from app.models.user import User

from app.schemas.admin import FileStatus
from app.schemas.common import APIResponse

from app.security.permissions import RequireRole
from app.security.dependencies import GetUser

from app.agents import instansiate_vector_db
from app.agents.database import ChromaVectorDatabase

router = APIRouter(prefix="/v1/admin", tags=["Admin"], dependencies=[Depends(RequireRole("admin"))])


@router.post("/insertdoc", response_model=APIResponse[FileStatus], status_code=201)
def insert_document(
    request: Request,
    file: UploadFile = File(), 
    user: User = Depends(GetUser()), 
    session: Session = Depends(get_db),
):
    
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    base_dir = Path("agents") / "database" / "KASBI_DOCUMENTS"
    base_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / safe_name

    document = Document(
        filename=safe_name,
        filepath=file_path,
        user_id=user.id,
        status="pending"
    )

    session.add(document)
    session.commit()

    vector_db = instansiate_vector_db(request.app)["vector_db"]

    vector_db.insert_documents([file_path])

    return APIResponse(status_code=201, message="Insert pending", data={"status": "pending"})