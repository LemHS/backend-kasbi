from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(default="user")


class LoginRequest(BaseModel):
    email: Optional[EmailStr]
    username: Optional[str]
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    role: str
    username: str


class RefreshRequest(BaseModel):
    refresh_token: str