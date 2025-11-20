from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.base import async_session_factory
from src.infrastructure.repositories import UserRepository, EmployeeRepository, TeamRepository
from src.application.services import UserService


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


def get_team_repository(session: AsyncSession = Depends(get_session)) -> TeamRepository:
    return TeamRepository(session)

def get_user_service(
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    team_repository: TeamRepository = Depends(get_team_repository)
) -> UserService:
    return UserService(employee_repository, user_repository, team_repository)
