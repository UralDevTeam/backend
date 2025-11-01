from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID
from uuid6 import uuid7

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base

if TYPE_CHECKING:
    from .employee import EmployeeOrm


class TeamOrm(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid7
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("teams.id")
    )

    leader_employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
        , unique=True
    )

    parent: Mapped[Optional["TeamOrm"]] = relationship(
        "TeamOrm", back_populates="children", remote_side="TeamOrm.id"
    )
    children: Mapped[list["TeamOrm"]] = relationship(
        "TeamOrm", back_populates="parent", cascade="all, delete-orphan"
    )

    members: Mapped[list["EmployeeOrm"]] = relationship(
        "EmployeeOrm",
        back_populates="team",
        foreign_keys="EmployeeOrm.team_id",
    )

    leader: Mapped["EmployeeOrm"] = relationship(
        "EmployeeOrm",
        back_populates="leading_team",
        uselist=False,
        primaryjoin="TeamOrm.leader_employee_id == EmployeeOrm.id",
        foreign_keys="TeamOrm.leader_employee_id",
    )
