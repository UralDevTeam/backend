from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Employee, Team, StatusHistory, Position
from src.infrastructure.db.models import EmployeeOrm, TeamOrm, PositionOrm, StatusHistoryOrm


class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: UUID) -> Employee:
        select_employee_stmt = select(EmployeeOrm).where(EmployeeOrm.id == id)
        employee_orm: EmployeeOrm = (await self._session.execute(select_employee_stmt)).scalar_one()
        # команда
        team_orm: TeamOrm = (await self._session.execute(select(TeamOrm).where(TeamOrm.id == employee_orm.team_id))).scalar_one()
        team = Team.model_validate(team_orm)
        # начальник
        # статус
        status_history_orm: list[StatusHistoryOrm] = (await self._session.execute(select(StatusHistoryOrm).where(StatusHistoryOrm.employee_id == employee_orm.id))).scalars().all()
        status_history = [StatusHistory.model_validate(status_history_orm) for status_history_orm in status_history_orm]
        # должность
        position_orm: PositionOrm = (await self._session.execute(
            select(PositionOrm).where(PositionOrm.id == employee_orm.position_id))).scalar_one()
        position = Position.model_validate(position_orm)
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

