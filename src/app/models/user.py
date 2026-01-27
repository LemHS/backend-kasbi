from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

from app.models.base import TimestampedModel, IDModel
from app.models.role import UserRole

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.document import Document
    from app.models.history import Thread

class User(IDModel, TimestampedModel, table=True):
    __tablename__ = "users"

    username: str = Field(index=True, nullable=False, unique=True)
    email: str = Field(index=True, nullable=False, unique=True)
    full_name: Optional[str] = Field(default=None, nullable=True)
    hashed_password: str
    is_active: bool = Field(default=True, nullable=False)
    token_version: int = Field(default=1, nullable=False)
    last_password_change: Optional[datetime] = Field(default=None)

    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRole)
    documents: List["Document"] = Relationship(back_populates="user")
    threads: List["Thread"] = Relationship(back_populates="user")