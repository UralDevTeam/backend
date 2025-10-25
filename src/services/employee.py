from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.db.models import EmployeeOrm, TeamOrm


class EmployeeService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find(
        self,
        id: UUID,
    ):
        stmt = (
            select(EmployeeOrm)
            .where(EmployeeOrm.id == id)
            .options(
                # команда
                selectinload(EmployeeOrm.team)
                .selectinload(TeamOrm.leader),
                # должность
                selectinload(EmployeeOrm.position),
                # история статусов
                selectinload(EmployeeOrm.status_history),
                # команда, которой он лидер
                selectinload(EmployeeOrm.leading_team),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
