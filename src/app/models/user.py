from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

from models.base import TimestampedModel, IDModel
from models.role import UserRole

if TYPE_CHECKING:
    from models.role import Role

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