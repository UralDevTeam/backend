from pydantic import BaseModel, AliasChoices, Field, ConfigDict
from typing import List, Optional, Literal
from uuid import UUID
from datetime import date

from src.domain.models import Employee, Team
from src.domain.utils.user import (
    build_full_name,
    build_short_name,
    resolve_role,
    resolve_grade,
    resolve_experience,
    resolve_status,
    resolve_team,
    resolve_boss_id
)

class EmployeeCreatePayload(BaseModel):
    first_name: str
    middle_name: str
    last_name: str | None = None
    birth_date: date
    hire_date: date
    city: str | None = None
    phone: str | None = None
    mattermost: str | None = None
    tg: str | None = None
    about_me: str | None = Field(
        default=None,
        validation_alias=AliasChoices("aboutMe", "about_me"),
        serialization_alias="aboutMe",
    )
    legal_entity: str | None = None
    department: str | None = None
    position: str
    team: str


class UserCreatePayload(BaseModel):
    email: str
    password: str
    role: Literal["admin", "user"] = "user"
    employee: EmployeeCreatePayload

class UserUpdatePayload(BaseModel):
    city: Optional[str] = None
    phone: Optional[str] = None
    mattermost: Optional[str] = None
    tg: Optional[str] = None
    about_me: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("aboutMe", "about_me"),
        serialization_alias="aboutMe",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

class UserLinkDTO(BaseModel):
    id: str
    fullName: str
    shortName: str


class UserDTO(BaseModel):
    id: str
    fio: str
    birthday: str
    team: List[str]
    boss: Optional[UserLinkDTO]
    role: str
    grade: str
    experience: int
    status: str
    city: str | None = None
    email: str
    phone: str | None
    mattermost: str | None
    tg: str | None
    aboutMe: str
    legalEntity: str | None = None
    department: str | None = None
    isAdmin: bool

    @classmethod
    def from_employee(
        cls,
        employee: Employee,
        boss: Employee | None,
        is_admin: bool,
        team_lookup: dict[UUID, Team],
    ) -> "UserDTO":
        return cls(
            id=str(employee.id),
            fio=build_full_name(employee),
            birthday=employee.birth_date.isoformat() if employee.birth_date else "",
            team=resolve_team(employee, team_lookup),
            boss=(
                UserLinkDTO(
                    id=str(boss.id),
                    fullName=build_full_name(boss),
                    shortName=build_short_name(boss),
                )
                if boss
                else None
            ),
            role=resolve_role(employee),
            grade=resolve_grade(employee),
            experience=resolve_experience(employee),
            status=resolve_status(employee),
            city=employee.city or "",
            email=employee.email,
            phone=employee.phone,
            mattermost=employee.mattermost,
            tg=employee.tg,
            aboutMe=employee.about_me or "",
            legalEntity=employee.legal_entity,
            department=employee.department,
            isAdmin=is_admin,
        )
