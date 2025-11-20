# src/services/user_service.py
from uuid import UUID

from src.application.dto import UserDTO, UserUpdatePayload
from src.domain.models import User
from src.infrastructure.repositories.employee import EmployeeRepository
from src.infrastructure.repositories.user import UserRepository
from src.infrastructure.repositories.team import TeamRepository
from src.utils.user import (
    build_team_lookup, resolve_boss_id
)


class UserService:
    def __init__(self, employee_repo: EmployeeRepository, user_repo: UserRepository, team_repo: TeamRepository):
        self.employee_repo = employee_repo
        self.user_repo = user_repo
        self.team_repo = team_repo

    async def list_users(self) -> list[UserDTO]:
        employees = await self.employee_repo.get_all()
        teams = await self.team_repo.get_all()
        lookup = build_team_lookup(teams)

        employees_by_id = {e.id: e for e in employees}
        employees_sorted = sorted(employees, key=lambda e: e.last_name.lower())

        result = []

        for emp in employees_sorted:
            boss_id = resolve_boss_id(emp, lookup)
            boss = employees_by_id.get(boss_id) if boss_id else None

            user = await self.user_repo.find_by_email(emp.email)
            is_admin = bool(user and user.role == "admin")

            result.append(
                UserDTO.from_employee(emp, boss=boss, is_admin=is_admin, team_lookup=lookup)
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

        user = await self.user_repo.find_by_email(emp.email)
        is_admin = bool(user and user.role == "admin")

        return UserDTO.from_employee(emp, boss=boss, is_admin=is_admin, team_lookup=lookup)

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
            is_admin=(current_user.role == "admin"),
            team_lookup=lookup
        )

    async def update_me(self, current_user: User, payload: UserUpdatePayload):
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        emp = await self.employee_repo.get_by_email(current_user.email)
        if not emp:
            return None

        if update_data:
            emp = await self.employee_repo.update_partial(emp.id, update_data)

        teams = await self.team_repo.get_all()
        team_lookup = build_team_lookup(teams)
        boss_id = resolve_boss_id(emp, team_lookup)
        boss = await self.employee_repo.get_by_id(boss_id) if boss_id else None

        return UserDTO.from_employee(
            emp,
            boss=boss,
            is_admin=(current_user.role == "admin"),
            team_lookup=team_lookup,
        )
