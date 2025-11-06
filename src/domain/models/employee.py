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
    last_name: str
    email: str
    birth_date: date
    hire_date: date
    city: str
    phone: str
    mattermost: str
    about_me: str | None = None
    position: Position | None = None
    team: Team | None = None
    status_history: list[StatusHistory] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")
