from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Team
from src.infrastructure.db.models import TeamOrm


class TeamRepository:
    """Работа с таблицей teams."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(self) -> list[Team]:
        stmt = select(TeamOrm)
        result = await self._session.execute(stmt)
        teams: Sequence[TeamOrm] = result.scalars().all()
        return [Team.model_validate(team) for team in teams]