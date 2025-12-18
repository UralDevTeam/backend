"""Test fixtures and configuration for pytest."""
import asyncio
import os
import sqlalchemy
from datetime import date
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid6 import uuid7

from src.domain.models import User, Employee, Team, Position, EmployeeStatus
from src.infrastructure.db.models import Base, TeamOrm
from src.infrastructure.repositories.user import UserRepository
from src.infrastructure.repositories.employee import EmployeeRepository
from src.infrastructure.repositories.team import TeamRepository
from src.infrastructure.repositories.position import PositionRepository
from src.infrastructure.repositories.avatar import AvatarRepository
from src.application.services.user import UserService
from src.application.services.avatar import AvatarService


# Test database URL - use PostgreSQL for testing to support all features
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5433/test_db"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests with CASCADE for circular dependencies
    async with engine.begin() as conn:
        # Drop tables manually with CASCADE to handle circular dependencies
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS status_history CASCADE"))
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS avatars CASCADE"))
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS employees CASCADE"))
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS teams CASCADE"))
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS positions CASCADE"))
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS users CASCADE"))
    
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_repo(session: AsyncSession) -> UserRepository:
    """Create a UserRepository instance."""
    return UserRepository(session)


@pytest_asyncio.fixture
async def employee_repo(session: AsyncSession) -> EmployeeRepository:
    """Create an EmployeeRepository instance."""
    return EmployeeRepository(session)


@pytest_asyncio.fixture
async def team_repo(session: AsyncSession) -> TeamRepository:
    """Create a TeamRepository instance."""
    return TeamRepository(session)


@pytest_asyncio.fixture
async def position_repo(session: AsyncSession) -> PositionRepository:
    """Create a PositionRepository instance."""
    return PositionRepository(session)


@pytest_asyncio.fixture
async def avatar_repo(session: AsyncSession) -> AvatarRepository:
    """Create an AvatarRepository instance."""
    return AvatarRepository(session)


@pytest_asyncio.fixture
async def user_service(
    employee_repo: EmployeeRepository,
    position_repo: PositionRepository,
    user_repo: UserRepository,
    team_repo: TeamRepository,
) -> UserService:
    """Create a UserService instance with all dependencies."""
    return UserService(employee_repo, position_repo, user_repo, team_repo)


@pytest_asyncio.fixture
async def avatar_service(avatar_repo: AvatarRepository) -> AvatarService:
    """Create an AvatarService instance."""
    return AvatarService(avatar_repo)


@pytest_asyncio.fixture
async def sample_position(position_repo: PositionRepository, session: AsyncSession) -> Position:
    """Create a sample position for testing."""
    position = await position_repo.get_or_create(title="Software Engineer")
    await session.commit()
    return position


@pytest_asyncio.fixture
async def sample_team(
    team_repo: TeamRepository, 
    employee_repo: EmployeeRepository,
    position_repo: PositionRepository,
    session: AsyncSession
) -> Team:
    """Create a sample team for testing with a valid leader employee."""
    # First, create a position for the leader
    position = await position_repo.get_or_create(title="Team Leader")
    
    # Create a placeholder leader employee (without team assignment yet)
    leader_id = uuid7()
    team_id = uuid7()
    
    # Insert team and employee in a way that satisfies circular dependencies
    # We'll use raw SQL to insert both at once within a deferred constraint transaction
    await session.execute(
        sqlalchemy.text(
            "INSERT INTO teams (id, name, parent_id, leader_employee_id) "
            "VALUES (:team_id, :name, NULL, :leader_id)"
        ),
        {"team_id": team_id, "name": "Development", "leader_id": leader_id}
    )
    
    await session.execute(
        sqlalchemy.text(
            "INSERT INTO employees (id, first_name, middle_name, last_name, email, "
            "birth_date, hire_date, team_id, position_id, is_birthyear_visible) "
            "VALUES (:id, :first_name, :middle_name, :last_name, :email, "
            ":birth_date, :hire_date, :team_id, :position_id, :is_birthyear_visible)"
        ),
        {
            "id": leader_id,
            "first_name": "Team",
            "middle_name": "Leader",
            "last_name": "Boss",
            "email": "leader@example.com",
            "birth_date": date(1985, 1, 1),
            "hire_date": date(2015, 1, 1),
            "team_id": team_id,
            "position_id": position.id,
            "is_birthyear_visible": True,
        }
    )
    
    await session.flush()
    
    # Fetch and return the team
    stmt = sqlalchemy.select(TeamOrm).where(TeamOrm.id == team_id)
    result = await session.execute(stmt)
    team_orm = result.scalar_one()
    return Team.model_validate(team_orm)


@pytest_asyncio.fixture
async def sample_user(user_repo: UserRepository, session: AsyncSession) -> User:
    """Create a sample user for testing."""
    user = User(
        id=uuid7(),
        email="test@example.com",
        password_hash="$2b$12$hash",
        role="user",
    )
    created_user = await user_repo.create(user)
    await session.commit()
    return created_user


@pytest_asyncio.fixture
async def admin_user(user_repo: UserRepository, session: AsyncSession) -> User:
    """Create a sample admin user for testing."""
    user = User(
        id=uuid7(),
        email="admin@example.com",
        password_hash="$2b$12$hash",
        role="admin",
    )
    created_user = await user_repo.create(user)
    await session.commit()
    return created_user


@pytest_asyncio.fixture
async def sample_employee(
    employee_repo: EmployeeRepository,
    sample_team: Team,
    sample_position: Position,
    session: AsyncSession,
) -> Employee:
    """Create a sample employee for testing."""
    employee_id = uuid7()
    employee_data = {
        "id": employee_id,
        "first_name": "John",
        "middle_name": "Michael",
        "last_name": "Doe",
        "email": "test@example.com",
        "birth_date": date(1990, 1, 1),
        "is_birthyear_visible": True,
        "hire_date": date(2020, 1, 1),
        "city": "Moscow",
        "phone": "+79001234567",
        "mattermost": "@johndoe",
        "tg": "@johndoe",
        "about_me": "Software Engineer",
        "legal_entity": "Company LLC",
        "department": "Engineering",
        "position_id": sample_position.id,
        "team_id": sample_team.id,
    }
    
    employee = await employee_repo.create(employee_data)
    
    # Set initial status
    await employee_repo.set_status(employee_id, EmployeeStatus.ACTIVE)
    
    await session.commit()
    
    # Reload to get all relationships
    return await employee_repo.get_by_id(employee_id)


@pytest_asyncio.fixture
async def admin_employee(
    employee_repo: EmployeeRepository,
    sample_team: Team,
    sample_position: Position,
    session: AsyncSession,
) -> Employee:
    """Create a sample admin employee for testing."""
    employee_id = uuid7()
    employee_data = {
        "id": employee_id,
        "first_name": "Admin",
        "middle_name": "Super",
        "last_name": "User",
        "email": "admin@example.com",
        "birth_date": date(1985, 1, 1),
        "is_birthyear_visible": True,
        "hire_date": date(2018, 1, 1),
        "city": "Moscow",
        "phone": "+79009999999",
        "position_id": sample_position.id,
        "team_id": sample_team.id,
    }
    
    employee = await employee_repo.create(employee_data)
    await employee_repo.set_status(employee_id, EmployeeStatus.ACTIVE)
    await session.commit()
    
    return await employee_repo.get_by_id(employee_id)
