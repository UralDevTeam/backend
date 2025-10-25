from typing import Optional

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID
from uuid6 import uuid7
from datetime import date

from sqlalchemy import String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import Base


class EmployeeOrm(Base):
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True),
                                     primary_key=True,
                                     default=uuid7,
                                     )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    middle_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    mattermost: Mapped[str] = mapped_column(String, nullable=False)
    about_me: Mapped[str | None] = mapped_column(String)

    team_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )

    team: Mapped["Team"] = relationship(back_populates="members")
    position: Mapped[Optional["Position"]] = relationship(back_populates="employees")

    leading_team: Mapped[Optional["Team"]] = relationship(
        "Team", back_populates="leader", uselist=False
    )

    status_history: Mapped[list["EmployeeStatusHistory"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )