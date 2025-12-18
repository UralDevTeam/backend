# src/tests/factories.py
from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4
from uuid6 import uuid7

from src.infrastructure.db.models import EmployeeOrm, TeamOrm, UserOrm, PositionOrm  # поправь импорт


async def create_position(session: AsyncMock, title: str = "Developer") -> PositionOrm:
    pos = PositionOrm(id=uuid4(), title=title)
    session.add(pos)
    await session.flush()
    await session.refresh(pos)
    return pos


async def create_team(session: AsyncMock, name: str, leader_employee_id, parent_id=None) -> TeamOrm:
    team = TeamOrm(
        id=uuid4(),
        name=name,
        leader_employee_id=leader_employee_id,
        parent_id=parent_id,
    )
    session.add(team)
    await session.flush()
    await session.refresh(team)
    return team


async def create_employee(session: AsyncMock, *, email: str, team_id, position_id, first_name="John", last_name="Doe") -> EmployeeOrm:
    emp = EmployeeOrm(
        id=uuid7(),
        first_name=first_name,
        middle_name="X",
        last_name=last_name,
        object_id=None,
        birth_date=date(1990, 1, 1),
        hire_date=date(2020, 1, 1),
        city="Москва",
        email=email,
        phone=None,
        mattermost=None,
        tg=None,
        about_me=None,
        legal_entity=None,
        department=None,
        avatar=None,
        team_id=team_id,
        position_id=position_id,
    )
    session.add(emp)
    await session.flush()
    await session.refresh(emp)
    return emp


async def create_user_orm(session: AsyncMock, *, email: str, role: str = "user") -> UserOrm:
    user = UserOrm(
        id=uuid7(),
        email=email,
        password_hash="hashed",
        role=role,
        password_changed_at_ts=None,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user
