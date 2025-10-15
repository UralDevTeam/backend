from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("teams.team_id", ondelete="SET NULL")
    )
    leader_employee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("employees.employee_id", ondelete="SET NULL")
    )

    parent: Mapped["Team" | None] = relationship(
        "Team", back_populates="children"
    )
    children: Mapped[list["Team"]] = relationship(
        "Team", back_populates="parent", cascade="all, delete-orphan"
    )

    leader: Mapped["Employee" | None] = relationship(
        "Employee", back_populates="leading_team", foreign_keys=[leader_employee_id]
    )

    members: Mapped[list["Employee"]] = relationship(back_populates="team")