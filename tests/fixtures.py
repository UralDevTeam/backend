from typing import AsyncGenerator

import pytest
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.base import async_session_factory
from src.infrastructure.repositories import (
    EmployeeRepository,
    PositionRepository,
    TeamRepository,
    UserRepository,
)
from src.application.services import UserService

@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


@pytest.fixture
def user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest.fixture
def employee_repository(session: AsyncSession) -> EmployeeRepository:
    return EmployeeRepository(session)


@pytest.fixture
def position_repository(session: AsyncSession) -> PositionRepository:
    return PositionRepository(session)


@pytest.fixture
def team_repository(session: AsyncSession) -> TeamRepository:
    return TeamRepository(session)


@pytest.fixture
def user_service(
    employee_repository: EmployeeRepository,
    position_repository: PositionRepository,
    user_repository: UserRepository,
    team_repository: TeamRepository
) -> UserService:
    return UserService(employee_repository, position_repository, user_repository, team_repository)

# tests/conftest.py
from .factories import create_position, create_team, create_employee, create_user_orm

@pytest.fixture
def position_factory(db_session):
    async def factory(**kwargs):
        return await create_position(db_session, **kwargs)
    return factory

@pytest.fixture
def team_factory(db_session):
    async def factory(**kwargs):
        return await create_team(db_session, **kwargs)
    return factory

@pytest.fixture
def employee_factory(db_session):
    async def factory(**kwargs):
        return await create_employee(db_session, **kwargs)
    return factory

@pytest.fixture
def user_orm_factory(db_session):
    async def factory(**kwargs):
        return await create_user_orm(db_session, **kwargs)
    return factory
