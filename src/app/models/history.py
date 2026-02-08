from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List, Literal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, ForeignKeyConstraint

from app.models.base import TimestampedModel, IDModel


if TYPE_CHECKING:
    from app.models.user import User

class Agent(str, Enum):
    user = "user"
    chatbot = "chatbot"

class Thread(TimestampedModel, table=True):
    __tablename__ = "threads"

    user_id: int = Field(index=True, primary_key=True, foreign_key="users.id", nullable=False)
    thread_id: int = Field(index=True, primary_key=True, nullable=False)
    thread_title: str = Field(nullable=False, unique=False)

    user: "User" = Relationship(back_populates="threads")
    chats: List["Chat"] = Relationship(back_populates="thread", cascade_delete=True)


class Chat(IDModel, TimestampedModel, table=True):
    __tablename__ = "chats"

    role: Agent = Field(nullable=False, unique=False)
    message: str = Field(nullable=False, unique=False)
    thread_id: int = Field(index=True, nullable=True)
    user_id: int = Field(index=True, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "thread_id"],
            ["threads.user_id", "threads.thread_id"],
            ondelete="CASCADE"
        ),
    )

    thread: "Thread" = Relationship(back_populates="chats")