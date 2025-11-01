from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StatusHistory(BaseModel):
    id: UUID
    status: str
    started_at: datetime
    ended_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")

