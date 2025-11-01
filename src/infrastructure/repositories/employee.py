from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.models import Employee, Team, StatusHistory, Position
from src.infrastructure.db.models import EmployeeOrm, TeamOrm, PositionOrm, StatusHistoryOrm


class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: UUID) -> Optional[Employee]:
        # Используем selectinload для эффективной загрузки связанных данных
        select_employee_stmt = (
            select(EmployeeOrm)
            .where(EmployeeOrm.id == id)
            .options(
                selectinload(EmployeeOrm.team),
                selectinload(EmployeeOrm.position),
                selectinload(EmployeeOrm.status_history)
            )
        )

        result = await self._session.execute(select_employee_stmt)
        employee_orm: EmployeeOrm | None = result.scalar_one_or_none()

        if not employee_orm:
            return None

        # Команда
        team = None
        if employee_orm.team_id:
            team_orm: TeamOrm = (
                await self._session.execute(
                    select(TeamOrm).where(TeamOrm.id == employee_orm.team_id)
                )
            ).scalar_one_or_none()
            if team_orm:
                team = Team.model_validate(team_orm)

        # История статусов
        status_history_orms: list[StatusHistoryOrm] = (
            await self._session.execute(
                select(StatusHistoryOrm).where(StatusHistoryOrm.employee_id == employee_orm.id)
            )
        ).scalars().all()
        status_history = [
            StatusHistory.model_validate(sh_orm) for sh_orm in status_history_orms
        ]

        # Должность
        position = None
        if employee_orm.position_id:
            position_orm: PositionOrm = (
                await self._session.execute(
                    select(PositionOrm).where(PositionOrm.id == employee_orm.position_id)
                )
            ).scalar_one_or_none()
            if position_orm:
                position = Position.model_validate(position_orm)

        # Начальник (если есть связь)
        manager = None
        if hasattr(employee_orm, 'manager_id') and employee_orm.manager_id:
            manager_orm: EmployeeOrm = (
                await self._session.execute(
                    select(EmployeeOrm).where(EmployeeOrm.id == employee_orm.manager_id)
                )
            ).scalar_one_or_none()
            if manager_orm:
                # Для начальника создаем упрощенную модель или рекурсивно вызываем get_by_id
                manager = await self.get_by_id(manager_orm.id)

        return Employee(
            id=employee_orm.id,
            first_name=employee_orm.first_name,
            middle_name=employee_orm.middle_name,
            last_name=employee_orm.last_name,
            birth_date=employee_orm.birth_date,
            hire_date=employee_orm.hire_date,
            city=employee_orm.city,
            phone=employee_orm.phone,
            mattermost=employee_orm.mattermost,
            about_me=employee_orm.about_me,
            position=position,
            team=team,
            status_history=status_history,
        )