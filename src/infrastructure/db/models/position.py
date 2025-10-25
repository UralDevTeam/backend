from uuid import UUID
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from src.infrastructure.db.models.base import Base


class PositionOrm(Base):
    __tablename__ = "positions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True),
                                     primary_key=True,
                                     default=uuid7,
                                     )
    title: Mapped[str] = mapped_column(String, nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="status_history")