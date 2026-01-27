from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List, Literal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

from app.models.base import TimestampedModel, IDModel


if TYPE_CHECKING:
    from app.models.user import User

class DocumentStatus(str, Enum):
    pending = "pending"
    done = "done"


class Document(IDModel, TimestampedModel, table=True):
    __tablename__ = "documents"

    filename: str = Field(index=True, nullable=False, unique=True)
    filepath: str = Field(index=True, nullable=False, unique=True)
    user_id: int = Field(index=True, foreign_key="users.id", nullable=False)
    status: DocumentStatus = Field(default="pending", nullable=False)

    user: "User" = Relationship(back_populates="documents")