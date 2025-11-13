from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from typing import AsyncGenerator, Dict, List, Optional, Set
from src.infrastructure.repositories.employee import EmployeeRepository
from src.infrastructure.repositories.user import UserRepository
from src.infrastructure.repositories.team import TeamRepository
from src.infrastructure.db.base import async_session_factory
from src.api.auth import get_current_user
from src.domain.models import Team
from src.domain.models.user import User

router = APIRouter()


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
    experience: int  # days
    status: str
    city: str | None = None
    email: str
    phone: str | None
    mattermost: str | None
    tg: str | None
    aboutMe: str
    isAdmin: bool


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


def _build_full_name(employee) -> str:
    parts = [
        getattr(employee, "last_name", None),
        getattr(employee, "first_name", None),
        getattr(employee, "middle_name", None),
    ]
    return " ".join(part for part in parts if part).strip()


def _build_short_name(employee) -> str:
    initials: List[str] = []
    first_name = getattr(employee, "first_name", "")
    middle_name = getattr(employee, "middle_name", "")
    last_name = getattr(employee, "last_name", "")
    if first_name:
        initials.append(f"{first_name[0]}.")
    if middle_name:
        initials.append(f"{middle_name[0]}.")
    initials_part = " ".join(initials).strip()
    if last_name:
        return f"{last_name} {initials_part}".strip()
    return initials_part


def _build_team_lookup(teams: List[Team]) -> Dict[UUID, Team]:
    return {team.id: team for team in teams}


def _collect_team_path(team: Team | None, team_lookup: Dict[UUID, Team]) -> List[Team]:
    path: List[Team] = []
    visited: Set[UUID] = set()
    current = team
    while current and current.id not in visited:
        path.append(current)
        visited.add(current.id)
        if current.parent_id is None:
            break
        current = team_lookup.get(current.parent_id)
    return path


def _resolve_team(employee, team_lookup: Dict[UUID, Team]) -> List[str]:
    team = getattr(employee, "team", None)
    if not team:
        return []

    team_lookup.setdefault(team.id, team)
    path = list(reversed(_collect_team_path(team, team_lookup)))
    names = [node.name for node in path if getattr(node, "name", None)]
    if len(names) > 1:
        return names[1:]
    return names


def _resolve_role(employee) -> str:
    position = getattr(employee, "position", None)
    if position and getattr(position, "title", None):
        return position.title
    return ""


def _resolve_grade(employee) -> str:
    title = _resolve_role(employee)
    if not title:
        return ""
    lower_title = title.lower()
    if lower_title.startswith("team lead"):
        return "Team Lead"
    for keyword in ("junior", "middle", "senior", "lead"):
        if lower_title.startswith(keyword):
            return keyword.capitalize()
    return ""


def _resolve_experience(employee) -> int:
    hire_date = getattr(employee, "hire_date", None)
    if isinstance(hire_date, date):
        return max((date.today() - hire_date).days, 0)
    return 0


def _resolve_status(employee) -> str:
    history = getattr(employee, "status_history", []) or []
    for record in history:
        if getattr(record, "ended_at", None) is None and getattr(record, "status", None):
            return record.status
    if history:
        sorted_history = sorted(
            [record for record in history if getattr(record, "started_at", None)],
            key=lambda rec: rec.started_at,
            reverse=True,
        )
        if sorted_history and getattr(sorted_history[0], "status", None):
            return sorted_history[0].status
    return "active"


def _resolve_boss_id(employee, team_lookup: Dict[UUID, Team]) -> Optional[UUID]:
    team = getattr(employee, "team", None)
    if not team:
        return None

    team_lookup.setdefault(team.id, team)
    current = team
    employee_id = getattr(employee, "id", None)
    visited: Set[UUID] = set()

    while current and current.id not in visited:
        visited.add(current.id)
        leader_id = getattr(current, "leader_employee_id", None)
        if leader_id and leader_id != employee_id:
            return leader_id
        if current.parent_id is None:
            break
        current = team_lookup.get(current.parent_id)

    return None


def _build_boss_link(boss) -> Optional[UserLinkDTO]:
    if not boss:
        return None
    return UserLinkDTO(
        id=str(getattr(boss, "id")),
        fullName=_build_full_name(boss),
        shortName=_build_short_name(boss),
    )


def _to_user_dto(
        employee,
        boss=None,
        *,
        is_admin: bool = False,
        team_lookup: Dict[UUID, Team] | None = None,
) -> UserDTO:
    team_lookup = team_lookup or {}
    return UserDTO(
        id=str(getattr(employee, "id")),
        fio=_build_full_name(employee),
        birthday=(
            employee.birth_date.isoformat()
            if getattr(employee, "birth_date", None)
            else ""
        ),
        team=_resolve_team(employee, team_lookup),
        boss=_build_boss_link(boss),
        role=_resolve_role(employee),
        grade=_resolve_grade(employee),
        experience=_resolve_experience(employee),
        status=_resolve_status(employee),
        city=getattr(employee, "city", "") or "",
        email=employee.email,
        phone=employee.phone,
        mattermost=employee.mattermost,
        tg=employee.tg,
        aboutMe=getattr(employee, "about_me", "") or "",
        isAdmin=is_admin,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД"""
    async with async_session_factory() as session:
        yield session


def _ensure_access(user: User) -> None:
    if user.role not in {"admin", "user"}:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/users", response_model=List[UserDTO])
async def get_users(db: AsyncSession = Depends(get_db)):
    repo = EmployeeRepository(db)
    user_repo = UserRepository(db)
    team_repo = TeamRepository(db)
    employees = await repo.get_all()
    teams = await team_repo.get_all()
    team_lookup = _build_team_lookup(teams)
    employees_by_id = {employee.id: employee for employee in employees}

    def _sort_key(employee):
        return _build_full_name(employee).lower()

    dtos: List[UserDTO] = []
    for employee in sorted(employees, key=_sort_key):
        boss = None
        boss_id = _resolve_boss_id(employee, team_lookup)
        if boss_id:
            boss = employees_by_id.get(boss_id)
        email = getattr(employee, "email", None)
        user = None
        if email:
            user = await user_repo.find_by_email(email)
        is_admin = bool(user and user.role == "admin")
        dtos.append(
            _to_user_dto(
                employee,
                boss=boss,
                is_admin=is_admin,
                team_lookup=team_lookup,
            )
        )
    return dtos


@router.get("/users/{user_id}", response_model=UserDTO)
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Получить пользователя по ID из PostgreSQL"""
    repo = EmployeeRepository(db)
    user_repo = UserRepository(db)
    team_repo = TeamRepository(db)
    teams = await team_repo.get_all()
    team_lookup = _build_team_lookup(teams)
    employee = await repo.get_by_id(user_id)

    if not employee:
        raise HTTPException(status_code=404, detail=f"User with id '{user_id}' not found")

    boss = None
    boss_id = _resolve_boss_id(employee, team_lookup)
    if boss_id:
        boss = await repo.get_by_id(boss_id)

    user = await user_repo.find_by_email(getattr(employee, "email", ""))
    is_admin = bool(user and user.role == "admin")

    return _to_user_dto(
        employee,
        boss=boss,
        is_admin=is_admin,
        team_lookup=team_lookup,
    )


@router.get("/me", response_model=UserDTO)
async def get_me(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    _ensure_access(current_user)

    repo = EmployeeRepository(db)
    team_repo = TeamRepository(db)
    teams = await team_repo.get_all()
    team_lookup = _build_team_lookup(teams)
    employee = await repo.get_by_email(current_user.email)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found for current user")

    boss = None
    boss_id = _resolve_boss_id(employee, team_lookup)
    if boss_id:
        boss = await repo.get_by_id(boss_id)

    is_admin = current_user.role == "admin"

    return _to_user_dto(
        employee,
        boss=boss,
        is_admin=is_admin,
        team_lookup=team_lookup,
    )


@router.put("/me", response_model=UserDTO)
async def update_me(
        payload: UserUpdatePayload,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    _ensure_access(current_user)

    repo = EmployeeRepository(db)
    team_repo = TeamRepository(db)
    teams = await team_repo.get_all()
    team_lookup = _build_team_lookup(teams)
    employee = await repo.get_by_email(current_user.email)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found for current user")

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

    if update_data:
        employee = await repo.update_partial(employee.id, update_data)
        await db.commit()

    boss = None
    boss_id = _resolve_boss_id(employee, team_lookup)
    if boss_id:
        boss = await repo.get_by_id(boss_id)

    is_admin = current_user.role == "admin"

    return _to_user_dto(
        employee,
        boss=boss,
        is_admin=is_admin,
        team_lookup=team_lookup,
    )
