from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AvatarOrm(Base):
    __tablename__ = "avatars"

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True
    )
    mime_type: Mapped[str] = mapped_column(String(length=128), default="image/png")
    image_small: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    image_large: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
