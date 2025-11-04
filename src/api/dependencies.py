from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.base import async_session_factory
from src.infrastructure.repositories import UserRepository


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()

def get_user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)
