from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Position
from src.infrastructure.db.models import PositionOrm


class PositionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_title(self, title: str) -> Optional[Position]:
        stmt = select(PositionOrm).where(PositionOrm.title == title)
        result = await self._session.execute(stmt)
        orm_obj: PositionOrm | None = result.scalar_one_or_none()

        if not orm_obj:
            return None

        return Position.model_validate(orm_obj)

    async def create(self, *, title: str) -> Position:
        position = PositionOrm(title=title)
        self._session.add(position)
        await self._session.flush()
        return Position.model_validate(position)

    async def get_or_create(self, *, title: str) -> Position:
        existing = await self.get_by_title(title)
        if existing:
            return existing

        return await self.create(title=title)