from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.base import async_session_factory
from src.infrastructure.repositories import (
    EmployeeRepository,
    PositionRepository,
    TeamRepository,
    UserRepository,
)
from src.application.services import AdImportService, UserService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_employee_repository(session: AsyncSession = Depends(get_session)) -> EmployeeRepository:
    return EmployeeRepository(session)


def get_position_repository(session: AsyncSession = Depends(get_session)) -> PositionRepository:
    return PositionRepository(session)


def get_team_repository(session: AsyncSession = Depends(get_session)) -> TeamRepository:
    return TeamRepository(session)

def get_user_service(
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    position_repository: PositionRepository = Depends(get_position_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    team_repository: TeamRepository = Depends(get_team_repository)
) -> UserService:
    return UserService(employee_repository, position_repository, user_repository, team_repository)


def get_ad_import_service(
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    position_repository: PositionRepository = Depends(get_position_repository),
    team_repository: TeamRepository = Depends(get_team_repository),
) -> AdImportService:
    return AdImportService(employee_repository, position_repository, team_repository)
