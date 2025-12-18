from uuid import UUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from src.infrastructure.db.models.base import Base, GUID
from src.infrastructure.db.models.employee import EmployeeOrm


class PositionOrm(Base):
    __tablename__ = "positions"

    id: Mapped[UUID] = mapped_column(GUID,
                                     primary_key=True,
                                     default=uuid7,
                                     )
    title: Mapped[str] = mapped_column(String, nullable=False)

    employees: Mapped[list["EmployeeOrm"]] = relationship(
        "EmployeeOrm",
        back_populates="position",
        foreign_keys="EmployeeOrm.position_id",
    )