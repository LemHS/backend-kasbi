from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    ADMIN_EMAILS: str
    ADMIN_PASS: str

    JWT_SECRET_KEY: str
    JWT_REFRESH_KEY: str
    JWT_HASHING_SCHEME: str
    ACCESS_EXPIRE: int
    REFRESH_EXPIRE: int
    PASSWORD_HASHING_SCHEME: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    VECTOR_DB_DIRECTORY: str
    EMBEDDING_MODEL: str
    RERANK_MODEL: str
    
    GROQ_API_KEY: str
    OPEN_ROUTER_API_KEY: str
    OPEN_ROUTER_MODEL: str
    
    ALLOWED_ORIGINS: str

    ACCESS_TOKEN: str
    VERSION: str
    PHONE_NUMBER_ID: str
    VERIFY_TOKEN: str

    @field_validator("ADMIN_EMAILS")
    def parse_admin_emails(cls, v: str) -> List[str]:
        return v.split(",") if v else []
    
    @field_validator("ADMIN_PASS")
    def parse_admin_pass(cls, v: str) -> List[str]:
        return v.split(",") if v else []
    
    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(",") if v else []
    
    @field_validator("VECTOR_DB_DIRECTORY")
    def parse_allowed_vector_db_directory(cls, v: str) -> Path:
        return Path(v).resolve()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
