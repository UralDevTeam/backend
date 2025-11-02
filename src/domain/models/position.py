from pydantic import BaseModel, ConfigDict
from uuid import UUID

class Position(BaseModel):
    id: UUID
    title: str

    model_config = ConfigDict(from_attributes=True)
