from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

from app.models.base import IDModel, TimestampedModel

if TYPE_CHECKING:
    from app.models.user import User

class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="roles.id", primary_key=True)


class Role(IDModel, TimestampedModel, table=True):
    __tablename__ = "roles"

    name: str = Field(index=True, nullable=False, unique=True)
    description: Optional[str] = Field(default=None, nullable=True)

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)