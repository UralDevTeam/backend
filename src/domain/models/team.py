from uuid import UUID
from pydantic import BaseModel, ConfigDict


class Team(BaseModel):
    id: UUID
    name: str
    parent_id: int
    leader_employee_id: int

    model_config = ConfigDict(from_attributes=True)
