from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date

from src.domain.models import Position, Team, StatusHistory


class Employee(BaseModel):
    id: UUID
    first_name: str
    middle_name: str
    last_name: str
    birth_date: date
    hire_date: date
    city: str
    phone: str
    mattermost: str
    about_me: str
    position: Position
    team: Team
    status_history: list[StatusHistory]

    model_config = ConfigDict(from_attributes=True, extra="ignore")
