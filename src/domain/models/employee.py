from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date

from .position import Position
from .team import Team
from .status_history import StatusHistory



class Employee(BaseModel):
    id: UUID
    first_name: str
    middle_name: str
    last_name: str | None
    object_id: str | None = None
    birth_date: date
    is_birthyear_visible: bool = False
    hire_date: date
    city: str | None = None
    email: str
    phone: str | None = None
    mattermost: str | None = None
    tg: str | None = None
    about_me: str | None = None
    legal_entity: str | None = None
    department: str | None = None
    position: Position
    team: Team
    status_history: list[StatusHistory] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")
