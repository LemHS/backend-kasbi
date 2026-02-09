from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List, Literal, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey
from pgvector.sqlalchemy import Vector

from app.models.base import TimestampedModel, IDModel


if TYPE_CHECKING:
    from app.models.user import User

class DocumentStatus(str, Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


class Document(IDModel, TimestampedModel, table=True):
    __tablename__ = "documents"

    filename: str = Field(index=True, nullable=False, unique=True)
    filepath: str = Field(index=True, nullable=False, unique=True)
    user_id: int = Field(index=True, foreign_key="users.id", nullable=False)
    status: DocumentStatus = Field(default="pending", nullable=False)

    user: "User" = Relationship(back_populates="documents")
    document_vectors: "DocumentVector" = Relationship(back_populates="document", cascade_delete=True)

class DocumentVector(IDModel, TimestampedModel, table=True):
    __tablename__ = "document_vectors"

    dense_embedding: Any = Field(sa_type=Vector(384))
    content: str = Field(default=None, nullable=False)
    document_id: int = Field(index=True, foreign_key="documents.id", nullable=False, ondelete="CASCADE")

    
    document: "Document" = Relationship(back_populates="document_vectors")