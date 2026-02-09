import uuid
import os
from datetime import datetime, timezone

from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, Request, UploadFile, File
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.worker import celery_app

from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.role import Role

from app.schemas.admin import FileStatus, DocumentResponse, DeleteDocRequest, CreateUserRequest, DeleteUserRequest, UserRead, UpdateUserRequest, UserResponse
from app.schemas.common import APIResponse

from app.security.permissions import RequireRole
from app.security.dependencies import GetUser
from app.security.passwords import hash_password

from app.tasks import embed_document

super_admin_router = APIRouter(prefix="/v1/superadmin", tags=["Admin"], dependencies=[Depends(RequireRole("superadmin", "admin"))])
admin_router = APIRouter(prefix="/v1/admin", tags=["Admin"], dependencies=[Depends(RequireRole("admin"))])


MAX_FILE_SIZE = 5 * 1024 * 1024

@admin_router.post("/insertdoc", response_model=APIResponse[FileStatus], status_code=201)
def insert_document(
    file: UploadFile = File(), 
    user: User = Depends(GetUser()), 
    session: Session = Depends(get_db),
):
    document = session.exec(
        select(Document).where(Document.filename == file.filename)
    ).one_or_none()

    if document is not None:
        raise HTTPException(status_code=404, detail="Document with the same file name already exist") 

    file_content = file.file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE / 1024 / 1024}MB)"
        )
    
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    base_dir = Path("src/docs")
    base_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / safe_name

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    document = Document(
        filename=file.filename,
        filepath=str(file_path),
        user_id=user.id,
        status="pending"
    )

    session.add(document)
    session.commit()

    embed_document.delay(document.id, str(file_path))

    return APIResponse(status_code=201, message="Insert pending", data={"status": "pending"})

@admin_router.delete("/deldoc", response_model=APIResponse)
def del_documents(
    payload: DeleteDocRequest,
    session: Session = Depends(get_db)
) -> APIResponse:

    documents = session.exec(
        select(Document).where(Document.id == payload.document_id)
    ).one_or_none()

    if documents is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(documents.filepath)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file: {str(e)}"
            )


    session.delete(documents)
    session.commit()

    return APIResponse(
        status_code=200, 
        message="Document deleted successfully")


@admin_router.get("/documents", response_model=APIResponse[DocumentResponse])
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

@super_admin_router.post("/users", response_model=APIResponse[FileStatus], status_code=201)
def create_user(
    payload: CreateUserRequest,
    session: Session = Depends(get_db)
) -> APIResponse[UserRead]:
    
    user = session.exec(
        select(User).where(User.email == payload.email)
    ).one_or_none()

    if user:
        raise HTTPException(status_code=409, detail={"error_code": "email_taken", "message": "Email already exists"})
    
    admin_role = session.exec(
            select(Role).where(Role.name == "admin")
    ).one_or_none()

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        roles=admin_role,
        is_active=True,
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return APIResponse(status_code=201, message="User created", data=UserRead.model_validate(user))

@super_admin_router.delete("/users", response_model=APIResponse, status_code=201)
def del_user(
    payload: DeleteUserRequest,
    session: Session = Depends(get_db)
) -> APIResponse:
    
    user = session.exec(
        select(User).where(User.email == payload.email)
    ).one_or_none()

    if user is None:
        raise HTTPException(status_code=409, detail={"error_code": "user_missing", "message": "User doesn't exist"})
    
    session.delete(user)
    session.commit()

    return APIResponse(
        status_code=200, 
        message="Document deleted successfully")

@super_admin_router.get("/users", response_model=APIResponse[UserResponse])
def get_users(
    session: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 10,
    descending: bool = True,
) -> APIResponse[UserResponse]:

    results = session.exec(select(User).where(User.roles.contains(["admin"])).order_by(
        User.username.desc() if descending else User.username.asc()
    ).offset(offset).limit(limit)).all()
    return APIResponse(
        status_code=200, 
        message="User returned successfully", 
        data={
            "user_items": [
                {"id": user.id, "user_name": user.username, "user_email": user.email}
                for user in results
            ]
        })

@super_admin_router.put("/users/{user_id}", response_model=APIResponse[FileStatus], status_code=201)
def update_user(
    user_id,
    payload: UpdateUserRequest,
    session: Session = Depends(get_db),
) -> APIResponse[FileStatus]:
    
    user = session.exec(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    ).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail={"error_code": "user_not_found", "message": "User not found"})
    
    update_data = payload.model_dump()

    if "password" in update_data:
        user.hashed_password = hash_password(update_data.pop("password"))
        user.token_version += 1
        user.last_password_change = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return APIResponse(status_code=200, message="User updated", data=UserRead.model_validate(user))