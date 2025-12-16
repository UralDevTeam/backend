from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy import select, insert, update, func, delete
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

    async def find_by_name(
            self, name: str, *, parent_id: UUID | None = None
    ) -> Optional[Team]:
        normalized_name = " ".join(name.split()).lower()

        stmt = select(TeamOrm).where(
            func.lower(
                func.regexp_replace(func.trim(TeamOrm.name), r"\\s+", " ", "g")
            )
            == normalized_name
        )
        if parent_id is None:
            stmt = stmt.where(TeamOrm.parent_id.is_(None))
        else:
            stmt = stmt.where(TeamOrm.parent_id == parent_id)

        team = (await self._session.execute(stmt)).scalars().first()

        if not team:
            return None

        return Team.model_validate(team)

    async def find_by_parent_id(self, parent_id: UUID) -> list[Team]:
        stmt = select(TeamOrm).where(TeamOrm.parent_id == parent_id)
        teams = (await self._session.execute(stmt)).scalars().all()

        return [Team.model_validate(team) for team in teams]

    async def get_or_create(
            self, *, name: str, leader_employee_id: UUID, parent_id: UUID | None
    ) -> Team:
        normalized_name = " ".join(name.split())

        existing = await self.find_by_name(normalized_name, parent_id=parent_id)
        if existing:
            return existing

        return await self.create(
            name=normalized_name,
            leader_employee_id=leader_employee_id,
            parent_id=parent_id,
        )

    async def create(
            self, *, name: str, leader_employee_id: UUID, parent_id: UUID | None
    ) -> Team:
        normalized_name = " ".join(name.split())

        stmt = (
            insert(TeamOrm)
            .values(
                name=normalized_name,
                leader_employee_id=leader_employee_id,
                parent_id=parent_id,
            )
            .returning(TeamOrm)
        )

        team = (await self._session.execute(stmt)).scalar_one()
        await self._session.flush()

        return Team.model_validate(team)

    async def update_parent(self, team_id: UUID, parent_id: UUID | None) -> Team:
        stmt = (
            update(TeamOrm)
            .where(TeamOrm.id == team_id)
            .values(parent_id=parent_id)
            .returning(TeamOrm)
        )

        team = (await self._session.execute(stmt)).scalar_one()
        await self._session.flush()

        return Team.model_validate(team)

    async def update_leader(self, team_id: UUID, leader_employee_id: UUID) -> Team:
        stmt = (
            update(TeamOrm)
            .where(TeamOrm.id == team_id)
            .values(leader_employee_id=leader_employee_id)
            .returning(TeamOrm)
        )

        team = (await self._session.execute(stmt)).scalar_one()
        await self._session.flush()

        return Team.model_validate(team)
