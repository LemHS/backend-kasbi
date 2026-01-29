from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List, Literal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

from app.models.base import TimestampedModel, IDModel


if TYPE_CHECKING:
    from app.models.user import User


class Thread(IDModel, TimestampedModel, table=True):
    __tablename__ = "threads"

    thread_title: str = Field(nullable=False, unique=False)
    user_id: int = Field(index=True, foreign_key="users.id", nullable=False)

    user: "User" = Relationship(back_populates="threads")
    chat: "Chat" = Relationship(back_populates="thread")


class Chat(IDModel, TimestampedModel, table=True):
    __tablename__ = "chats"

    user_query: str = Field(index=True, nullable=False, unique=False)
    answer: str = Field(index=True, nullable=False, unique=False)
    thread_id: int = Field(index=True, foreign_key="threads.id", nullable=True)

    thread: "Thread" = Relationship(back_populates="chat")