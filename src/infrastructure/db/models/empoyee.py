from datetime import date

from sqlalchemy import BigInteger, String, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models import Team
from src.infrastructure.db.models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String)
    birth_date: Mapped[date | None] = mapped_column(Date)
    hire_date: Mapped[date | None] = mapped_column(Date)
    city: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    about_me: Mapped[str | None] = mapped_column(Text)

    team_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("teams.id", use_alter=True)
    )
    position_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("positions.id")
    )

    team: Mapped["Team" | None] = relationship(back_populates="members", foreign_keys=[team_id])
    position: Mapped["Position" | None] = relationship(back_populates="employees", foreign_keys=[position_id])

    leading_team: Mapped["Team" | None] = relationship(
        "Team", back_populates="leader", uselist=False, foreign_keys=[Team.leader_employee_id]
    )

    status_history: Mapped[list["EmployeeStatusHistory"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )