# src/services/user_service.py
from datetime import date
from typing import Literal, TypedDict
from uuid import UUID

from uuid6 import uuid7

from src.application.dto import AdminUserUpdatePayload, UserDTO, UserUpdatePayload
from src.domain.models import EmployeeStatus, User, Team, Employee
from src.infrastructure.repositories.position import PositionRepository
from src.infrastructure.repositories.employee import EmployeeRepository
from src.infrastructure.repositories.user import UserRepository
from src.infrastructure.repositories.team import TeamRepository
from src.utils.user import (
    build_team_lookup, resolve_boss_id
)


class EmployeeCreationData(TypedDict):
    first_name: str
    middle_name: str
    last_name: str | None
    birth_date: date
    is_birthyear_visible: bool
    hire_date: date
    city: str | None
    phone: str | None
    mattermost: str | None
    tg: str | None
    about_me: str | None
    legal_entity: str | None
    department: str | None
    position: str
    team: str


class UserService:
    def __init__(self, employee_repo: EmployeeRepository, position_repo: PositionRepository, user_repo: UserRepository,
                 team_repo: TeamRepository):
        self.employee_repo = employee_repo
        self.position_repo = position_repo
        self.user_repo = user_repo
        self.team_repo = team_repo

    async def list_users(self) -> list[UserDTO]:
        employees = await self.employee_repo.get_all()
        teams = await self.team_repo.get_all()
        lookup = build_team_lookup(teams)

        employees_by_id = {e.id: e for e in employees}
        employees_sorted = sorted(employees, key=lambda e: (e.last_name or "").lower())

        result = []

        for emp in employees_sorted:
            boss_id = resolve_boss_id(emp, lookup)
            boss = employees_by_id.get(boss_id) if boss_id else None

            result.append(
                UserDTO.from_employee(emp, boss=boss, is_admin=emp.is_admin, team_lookup=lookup)
            )

        return result

    async def get_user(self, user_id: UUID) -> UserDTO | None:
        emp = await self.employee_repo.get_by_id(user_id)
        if not emp:
            return None

        teams = await self.team_repo.get_all()
        lookup = build_team_lookup(teams)

        boss_id = resolve_boss_id(emp, lookup)
        boss = await self.employee_repo.get_by_id(boss_id) if boss_id else None
        return UserDTO.from_employee(emp, boss=boss, is_admin=emp.is_admin, team_lookup=lookup)

    async def get_me(self, current_user: User) -> UserDTO | None:
        emp = await self.employee_repo.get_by_email(current_user.email)
        if not emp:
            return None

        teams = await self.team_repo.get_all()
        lookup = build_team_lookup(teams)

        boss_id = resolve_boss_id(emp, lookup)
        boss = await self.employee_repo.get_by_id(boss_id) if boss_id else None

        return UserDTO.from_employee(
            emp,
            boss=boss,
            is_admin=emp.is_admin,
            team_lookup=lookup
        )

    async def update_me(self, current_user: User, payload: UserUpdatePayload):
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        status_value = update_data.pop("status", None)

        emp = await self.employee_repo.get_by_email(current_user.email)
        if not emp:
            return None

        if update_data:
            emp = await self.employee_repo.update_partial(emp.id, update_data)

        if status_value:
            await self.employee_repo.set_status(emp.id, EmployeeStatus(status_value))

        teams = await self.team_repo.get_all()
        team_lookup = build_team_lookup(teams)
        boss_id = resolve_boss_id(emp, team_lookup)
        boss = await self.employee_repo.get_by_id(boss_id) if boss_id else None

        return UserDTO.from_employee(
            emp,
            boss=boss,
            is_admin=emp.is_admin,
            team_lookup=team_lookup,
        )

    async def update_user(self, user_id: UUID, payload: AdminUserUpdatePayload) -> UserDTO | None:
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        status_value = update_data.pop("status", None)

        employee = await self.employee_repo.get_by_id(user_id)
        if not employee:
            return None

        original_email = employee.email

        position_title = update_data.pop("position", None)
        team_names = update_data.pop("team", None)

        if position_title:
            position = await self.position_repo.get_or_create(title=position_title)
            update_data["position_id"] = position.id

        if team_names:
            update_data["team_id"] = await self._resolve_team_id(employee, team_names)

        if update_data:
            employee = await self.employee_repo.update_partial(user_id, update_data)

        if status_value:
            await self.employee_repo.set_status(employee.id, EmployeeStatus(status_value))

        user = await self.user_repo.find_by_email(original_email)

        user_update_data = {}
        if "email" in update_data:
            user_update_data["email"] = update_data["email"]

        if user_update_data:
            if user:
                await self.user_repo.update_by_email(original_email, user_update_data)
            else:
                raise ValueError("User account not found for employee to update access")

        teams = await self.team_repo.get_all()
        team_lookup = build_team_lookup(teams)
        boss_id = resolve_boss_id(employee, team_lookup)
        boss = await self.employee_repo.get_by_id(boss_id) if boss_id else None

        return UserDTO.from_employee(
            employee,
            boss=boss,
            is_admin=employee.is_admin,
            team_lookup=team_lookup,
        )

    async def create_user(
            self,
            *,
            email: str,
            password_hash: str,
            role: Literal["admin", "user"],
            employee_payload: EmployeeCreationData,
            creator: User,
    ) -> UserDTO:
        if await self.user_repo.find_by_email(email):
            raise ValueError("User already registered")

        if await self.employee_repo.get_by_email(email):
            raise ValueError("Employee with the same email already exists")

        new_user = User(id=uuid7(), email=email, password_hash=password_hash)

        employee_data = employee_payload.copy()
        position_title = employee_data.pop("position")
        team_name = " ".join(employee_data.pop("team").split())

        if not team_name:
            raise ValueError("Team name cannot be empty")

        position = await self.position_repo.get_or_create(title=position_title)

        team = await self.team_repo.find_by_name(team_name, parent_id=None)
        if not team:
            creator_employee = await self.employee_repo.get_by_email(creator.email)
            if not creator_employee:
                raise ValueError("Creator employee record not found")

            team = await self.team_repo.create(
                name=team_name,
                leader_employee_id=creator_employee.id,
                parent_id=None,
            )

        employee_id = uuid7()

        employee_record = await self.employee_repo.create(
            {
                **employee_data,
                "id": employee_id,
                "email": email,
                "position_id": position.id,
                "team_id": team.id,
                "is_admin": role == "admin"
            }
        )

        await self.user_repo.create(new_user)

        teams = await self.team_repo.get_all()
        team_lookup = build_team_lookup(teams)
        boss_id = resolve_boss_id(employee_record, team_lookup)
        boss = await self.employee_repo.get_by_id(boss_id) if boss_id else None

        return UserDTO.from_employee(
            employee_record,
            boss=boss,
            is_admin= role == "admin",
            team_lookup=team_lookup,
        )

    async def delete_user(
        self,
        employee_id: UUID
    ) -> None:
        employee = await self.employee_repo.get_by_id(employee_id)
        employees_in_team = await self.employee_repo.get_by_team_id(employee.team.id)
        other_employees = [e for e in employees_in_team if e.id != employee.id]
        if employee.team.leader_employee_id == employee.id:
            if other_employees:
                raise ValueError(f"Нельзя удалить сотрудника '{employee.id}', "
                             f"потому что он лидер команды {employee.team.name}, и в его команде еще есть сотрудники")
            if await self._are_employees_in_teams_below(employee.team):
                raise ValueError(f"Нельзя удалить сотрудника '{employee.id}', "
                                 f"потому что в дочерних командах еще есть сотрудники")
        await self.user_repo.delete_by_email(employee.email)
        await self.employee_repo.delete_by_id(employee.id)

    async def _resolve_team_id(
        self,
        employee: Employee,
        team_names: list[str],
    ) -> UUID:
        # 2 валидных кейса:
        # 1) все команды существуют и идут в иерархическом порядке
        # 2) последней команды может не быть, тогда её создаём относительно последней команды

        if not team_names:
            raise ValueError("Team names cannot be empty")

        parent_team: Team | None = None
        team_names_len = len(team_names)

        for i, raw_name in enumerate(team_names):
            name = " ".join(raw_name.split())
            if not name:
                raise ValueError("Team name cannot be empty")

            parent_id = parent_team.id if parent_team else None
            team = await self.team_repo.find_by_name(name, parent_id=parent_id)

            if not team:
                if i != team_names_len - 1:
                    raise ValueError(f"Team '{name}' not found")
                team = await self.team_repo.create(
                    name=name,
                    leader_employee_id=employee.id,
                    parent_id=parent_id,
                )
            else:
                if i != 0 and team.parent_id != parent_team.id:
                    raise ValueError(
                        f"Team '{parent_team.name}' is not parent of team '{team.name}'"
                    )

            parent_team = team

        return parent_team.id

    async def _are_employees_in_teams_below(self, team: Team) -> bool:
        teams_below = await self.team_repo.find_by_parent_id(team.id)
        for child in teams_below:
            if await self._is_employees_in_team(child) or await self._are_employees_in_teams_below(child):
                return True
        return False

    async def _is_employees_in_team(
        self,
        team: Team,
    ) -> bool:
        return await self.employee_repo.get_by_team_id(team.id) != []
