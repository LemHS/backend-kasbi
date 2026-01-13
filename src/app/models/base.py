from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class TimestampedModel(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

class IDModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)