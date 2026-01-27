from pydantic import BaseModel, EmailStr, Field

class FileStatus(BaseModel):
    status: str

class DocumentResponse(BaseModel):
    document_id: str
    document_name: str