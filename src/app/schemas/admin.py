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

class DeleteRequest(BaseModel):
    document_id: int