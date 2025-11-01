from uuid import UUID
from pydantic import BaseModel, ConfigDict


class Team(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None = None
    leader_employee_id: UUID

    model_config = ConfigDict(from_attributes=True)
