from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime

class FileStatus(BaseModel):
    status: str

class DocumentItem(BaseModel):
    document_id: int
    document_name: str
    document_status: str
    time_upload: datetime
    user: str

class DocumentResponse(BaseModel):
    document_items: List[DocumentItem]

class DeleteDocRequest(BaseModel):
    document_id: int

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserItem(UserBase):
    id: int

class RoleBase(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        from_attributes = True

class CreateUserRequest(UserBase):
    password: str

class DeleteUserRequest(UserBase):
    pass

class UserResponse(BaseModel):
    user_items: List[UserItem]

class UpdateUserRequest(UserBase):
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None

class UserRead(UserBase):
    id: int
    is_active: bool
    roles: List[RoleBase]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True