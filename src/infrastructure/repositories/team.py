from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy import select, insert
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

    async def find_by_name(self, name: str) -> Optional[Team]:
        stmt = select(TeamOrm).where(TeamOrm.name == name)
        team = (await self._session.execute(stmt)).scalar_one_or_none()

        if not team:
            return None

        return Team.model_validate(team)

    async def create(
            self, *, name: str, leader_employee_id: UUID, parent_id: UUID | None
    ) -> Team:
        stmt = (
            insert(TeamOrm)
            .values(name=name, leader_employee_id=leader_employee_id, parent_id=parent_id)
            .returning(TeamOrm)
        )

        team = (await self._session.execute(stmt)).scalar_one()
        await self._session.flush()

        return Team.model_validate(team)
