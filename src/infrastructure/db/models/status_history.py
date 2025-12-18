from uuid import UUID
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from src.infrastructure.db.models.base import Base, GUID
from src.infrastructure.db.models.employee import EmployeeOrm


class StatusHistoryOrm(Base):
    __tablename__ = "status_history"

    id: Mapped[UUID] = mapped_column(GUID,
                                     primary_key=True,
                                     default=uuid7,
                                     )
    employee_id: Mapped[UUID] = mapped_column(
        GUID, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    employee: Mapped["EmployeeOrm"] = relationship(back_populates="status_history")