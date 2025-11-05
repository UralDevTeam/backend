import uuid
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: UUID = uuid.uuid4()
    email: str
    password_hash: str
    role: Literal["admin", "user"]

    model_config = ConfigDict(from_attributes=True)
