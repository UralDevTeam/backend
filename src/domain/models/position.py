from pydantic import BaseModel, ConfigDict
from uuid import UUID

class Position(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)
