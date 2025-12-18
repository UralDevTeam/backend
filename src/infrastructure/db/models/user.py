from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID
from uuid6 import uuid7

from sqlalchemy import String, ForeignKey, VARCHAR, DateTime, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base


class UserOrm(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid7
    )
    email: Mapped[str] = mapped_column(VARCHAR(255))
    password_hash: Mapped[str] = mapped_column(VARCHAR(255))
    role: Mapped[str] = mapped_column(VARCHAR(255))
    password_changed_at_ts: Mapped[int] = mapped_column(INTEGER, nullable=True)
