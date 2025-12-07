from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.models.status import EmployeeStatus


class StatusHistory(BaseModel):
    id: UUID
    status: EmployeeStatus
    started_at: datetime
    ended_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")
