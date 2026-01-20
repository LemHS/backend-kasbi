from pydantic import BaseModel, EmailStr, Field

class FileStatus(BaseModel):
    status: str