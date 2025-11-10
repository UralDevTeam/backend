from uuid import UUID
from typing import Any, Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.models import Employee, Team, StatusHistory, Position
from src.infrastructure.db.models import EmployeeOrm, TeamOrm, PositionOrm, StatusHistoryOrm


class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: UUID) -> Optional[Employee]:
        # Используем selectinload для эффективной загрузки связанных данных
        stmt = (
            select(EmployeeOrm)
            .where(EmployeeOrm.id == id)
            .options(
                selectinload(EmployeeOrm.team),
                selectinload(EmployeeOrm.position),
                selectinload(EmployeeOrm.status_history),
            )
        )

        result = await self._session.execute(stmt)
        employee_orm: EmployeeOrm | None = result.scalar_one_or_none()

        if not employee_orm:
            return None

        return self._to_domain(employee_orm)

    async def get_by_email(self, email: str) -> Optional[Employee]:
        stmt = (
            select(EmployeeOrm)
            .where(EmployeeOrm.email == email)
            .options(
                selectinload(EmployeeOrm.team),
                selectinload(EmployeeOrm.position),
                selectinload(EmployeeOrm.status_history),
            )
        )

        result = await self._session.execute(stmt)
        employee_orm: EmployeeOrm | None = result.scalar_one_or_none()

        if not employee_orm:
            return None

        return self._to_domain(employee_orm)

    async def get_all(self) -> list[Employee]:
        stmt = select(EmployeeOrm).options(
            selectinload(EmployeeOrm.team),
            selectinload(EmployeeOrm.position),
            selectinload(EmployeeOrm.status_history),
        )
        result = await self._session.execute(stmt)
        employee_orms: Sequence[EmployeeOrm] = result.scalars().all()
        return [self._to_domain(employee_orm) for employee_orm in employee_orms]

    async def update_partial(self, id: UUID, data: dict[str, Any]) -> Employee:
        if not data:
            employee = await self.get_by_id(id)
            if not employee:
                raise ValueError(f"Employee with id '{id}' not found")
            return employee

        stmt = (
            update(EmployeeOrm)
            .where(EmployeeOrm.id == id)
            .values(**data)
            .execution_options(synchronize_session="fetch")
        )
        await self._session.execute(stmt)
        await self._session.flush()

        employee = await self.get_by_id(id)
        if not employee:
            raise ValueError(f"Employee with id '{id}' not found")
        return employee

    def _to_domain(self, employee_orm: EmployeeOrm) -> Employee:
        team = Team.model_validate(employee_orm.team) if employee_orm.team else None
        position = (
            Position.model_validate(employee_orm.position)
            if employee_orm.position
            else None
        )
        status_history = [
            StatusHistory.model_validate(record)
            for record in (employee_orm.status_history or [])
        ]

        return Employee(
            id=employee_orm.id,
            first_name=employee_orm.first_name,
            middle_name=employee_orm.middle_name,
            last_name=employee_orm.last_name,
            email=employee_orm.email,
            birth_date=employee_orm.birth_date,
            hire_date=employee_orm.hire_date,
            city=employee_orm.city,
            phone=employee_orm.phone,
            mattermost=employee_orm.mattermost,
            tg=employee_orm.tg,
            about_me=employee_orm.about_me,
            position=position,
            team=team,
            status_history=status_history,
        )
