from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Avatar(BaseModel):
    employee_id: UUID
    mime_type: str
    image_small: bytes
    image_large: bytes

    model_config = ConfigDict(from_attributes=True)
