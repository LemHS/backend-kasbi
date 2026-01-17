from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: str

    ADMIN_EMAILS: str
    ADMIN_PASS: str

    JWT_SECRET_KEY: str
    JWT_REFRESH_KEY: str
    JWT_HASHING_SCHEME: str
    ACCESS_EXPIRE: int
    REFRESH_EXPIRE: int
    PASSWORD_HASHING_SCHEME: str
    
    GROQ_API_KEY: str
    OPEN_ROUTER_API_KEY: str
    
    ALLOWED_ORIGINS: str

    @field_validator("ADMIN_EMAILS")
    def parse_admin_emails(cls, v: str) -> List[str]:
        return v.split(",") if v else []
    
    @field_validator("ADMIN_PASS")
    def parse_admin_pass(cls, v: str) -> List[str]:
        return v.split(",") if v else []
    
    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(",") if v else []
    
    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
