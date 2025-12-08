from pydantic import BaseModel, AliasChoices, Field, ConfigDict
from typing import List, Optional, Literal
from uuid import UUID
from datetime import date

from src.domain.models import Employee, Team, EmployeeStatus
from src.domain.utils.user import (
    build_full_name,
    build_short_name,
    resolve_position,
    resolve_experience,
    resolve_status,
    resolve_team,
)


class PingResponse(BaseModel):
    ping: str


class AdImportResultDTO(BaseModel):
    imported: int


class DetailResponse(BaseModel):
    detail: str


class TeamDTO(BaseModel):
    id: UUID
    name: str
    parentId: UUID | None = None
    leaderEmployeeId: UUID

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_team(cls, team: Team) -> "TeamDTO":
        return cls(
            id=team.id,
            name=team.name,
            parentId=team.parent_id,
            leaderEmployeeId=team.leader_employee_id,
        )


class EmployeeCreatePayload(BaseModel):
    first_name: str = Field(
        validation_alias=AliasChoices("firstName", "first_name"),
        serialization_alias="firstName",
    )
    middle_name: str = Field(
        validation_alias=AliasChoices("middleName", "middle_name"),
        serialization_alias="middleName",
    )
    last_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("lastName", "last_name"),
        serialization_alias="lastName",
    )
    birth_date: date = Field(
        validation_alias=AliasChoices("birthDate", "birth_date"),
        serialization_alias="birthDate",
    )
    hire_date: date = Field(
        validation_alias=AliasChoices("hireDate", "hire_date"),
        serialization_alias="hireDate",
    )
    is_birthyear_visible: bool = Field(
        default=False,
        validation_alias=AliasChoices("isBirthyearVisible", "is_birthyear_visible"),
        serialization_alias="isBirthyearVisible",
    )
    city: str | None = None
    phone: str | None = None
    mattermost: str | None = None
    tg: str | None = None
    about_me: str | None = Field(
        default=None,
        validation_alias=AliasChoices("aboutMe", "about_me"),
        serialization_alias="aboutMe",
    )
    legal_entity: str | None = Field(
        default=None,
        validation_alias=AliasChoices("legalEntity", "legal_entity"),
        serialization_alias="legalEntity",
    )
    department: str | None = Field(
        default=None,
        validation_alias=AliasChoices("department", "department"),
        serialization_alias="department",
    )
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
    status: Optional[EmployeeStatus] = None
    is_birthyear_visible: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("isBirthyearVisible", "is_birthyear_visible"),
        serialization_alias="isBirthyearVisible",
    )
    about_me: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("aboutMe", "about_me"),
        serialization_alias="aboutMe",
    )
    birth_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("birthDate", "birth_date", "birthdate"),
        serialization_alias="birthDate",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class AdminUserUpdatePayload(UserUpdatePayload):
    first_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("firstName", "first_name"),
        serialization_alias="firstName",
    )
    middle_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("middleName", "middle_name"),
        serialization_alias="middleName",
    )
    last_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("lastName", "last_name"),
        serialization_alias="lastName",
    )
    birth_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("birthDate", "birth_date"),
        serialization_alias="birthDate",
    )
    hire_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("hireDate", "hire_date"),
        serialization_alias="hireDate",
    )
    email: Optional[str] = None
    legal_entity: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("legalEntity", "legal_entity"),
        serialization_alias="legalEntity",
    )
    department: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("department", "department"),
        serialization_alias="department",
    )
    position: Optional[str] = None
    team: list[str] = []
    is_admin: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("isAdmin", "is_admin"),
        serialization_alias="isAdmin",
    )


class UserLinkDTO(BaseModel):
    id: str
    fullName: str
    shortName: str


class UserDTO(BaseModel):
    id: str
    fio: str
    birthday: str
    isBirthyearVisible: bool
    team: List[str]
    boss: Optional[UserLinkDTO]
    position: str
    experience: int
    status: EmployeeStatus
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
        birthday = ""
        if employee.birth_date:
            birthday = (
                employee.birth_date.isoformat()
                if employee.is_birthyear_visible
                else employee.birth_date.strftime("%m-%d")
            )

        return cls(
            id=str(employee.id),
            fio=build_full_name(employee),
            birthday=birthday,
            isBirthyearVisible=employee.is_birthyear_visible,
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
            position=resolve_position(employee),
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
