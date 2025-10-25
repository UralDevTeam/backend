from typing import Optional
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from src.infrastructure.db.models.base import Base


class TeamOrm(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True),
                                     primary_key=True,
                                     default=uuid7,
                                     )
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("teams.id")
    )
    leader_employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )

    parent: Mapped[Optional["Team"]] = relationship(
        "Team", back_populates="children"
    )
    children: Mapped[list["Team"]] = relationship(
        "Team", back_populates="parent", cascade="all, delete-orphan"
    )

    leader: Mapped["Employee"] = relationship(
        "Employee", back_populates="leading_team"
    )
