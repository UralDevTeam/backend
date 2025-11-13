from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID
from uuid6 import uuid7
from datetime import date

from sqlalchemy import String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base

if TYPE_CHECKING:
    from .status_history import StatusHistoryOrm
    from .position import PositionOrm
    from .team import TeamOrm


class EmployeeOrm(Base):
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid7
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    middle_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String)
    mattermost: Mapped[str] = mapped_column(String)
    tg: Mapped[str] = mapped_column(String)
    about_me: Mapped[str | None] = mapped_column(String)
    legal_entity: Mapped[str | None] = mapped_column(String)
    department: Mapped[str | None] = mapped_column(String)

    team_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )

    team: Mapped["TeamOrm"] = relationship(
        "TeamOrm",
        back_populates="members",
        foreign_keys="EmployeeOrm.team_id",  # снимаем двусмысленность
    )

    position: Mapped[Optional["PositionOrm"]] = relationship(
        "PositionOrm",
        back_populates="employees",
    )

    leading_team: Mapped[Optional["TeamOrm"]] = relationship(
        "TeamOrm",
        back_populates="leader",
        uselist=False,
        primaryjoin="EmployeeOrm.id == TeamOrm.leader_employee_id",
        foreign_keys="TeamOrm.leader_employee_id",
    )

    status_history: Mapped[list["StatusHistoryOrm"]] = relationship(
        "StatusHistoryOrm",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
