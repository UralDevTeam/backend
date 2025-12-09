from datetime import date
from typing import List, Dict, Set, Optional
from uuid import UUID

from src.domain.models import Team, Employee, EmployeeStatus


def build_full_name(employee: Employee) -> str:
    parts = [
        employee.last_name,
        employee.first_name,
        employee.middle_name,
    ]
    return " ".join(part for part in parts if part).strip()


def build_short_name(employee: Employee) -> str:
    initials: List[str] = []
    if employee.first_name:
        initials.append(f"{employee.first_name[0]}.")
    if employee.middle_name:
        initials.append(f"{employee.middle_name[0]}.")
    return f"{employee.last_name} {' '.join(initials)}".strip()


def build_team_lookup(teams: List[Team]) -> Dict[UUID, Team]:
    return {team.id: team for team in teams}


def collect_team_path(team: Team | None, lookup: Dict[UUID, Team]) -> List[Team]:
    path: List[Team] = []
    visited: Set[UUID] = set()
    current = team

    while current and current.id not in visited:
        path.append(current)
        visited.add(current.id)
        if current.parent_id is None:
            break
        current = lookup.get(current.parent_id)
    return path


def resolve_team(employee: Employee, lookup: Dict[UUID, Team]) -> List[str]:
    team = employee.team
    if not team:
        return []
    lookup.setdefault(team.id, team)

    path = list(reversed(collect_team_path(team, lookup)))
    names = [node.name for node in path if node.name]
    return names[1:] if len(names) > 1 else names


def resolve_position(employee: Employee) -> str:
    position = employee.position
    return position.title if position and position.title else ""


def resolve_experience(employee: Employee) -> int:
    hire_date = employee.hire_date
    if isinstance(hire_date, date):
        return max((date.today() - hire_date).days, 0)
    return 0


def resolve_status(employee: Employee) -> EmployeeStatus:
    history = employee.status_history
    for record in history:
        if record.ended_at is None and record.status:
            return record.status

    if history:
        recent = sorted(
            (r for r in history if r.started_at),
            key=lambda r: r.started_at,
            reverse=True,
        )
        if recent and recent[0].status:
            return recent[0].status

    return EmployeeStatus.ACTIVE


def resolve_boss_id(employee: Employee, lookup: Dict[UUID, Team]) -> Optional[UUID]:
    team = employee.team
    if not team:
        return None

    current = team
    emp_id = employee.id

    while current:
        leader_id = current.leader_employee_id

        if leader_id and leader_id != emp_id:
            return leader_id

        if not current.parent_id:
            break

        current = lookup.get(current.parent_id)

        if current and current.id == team.id:
            break

    return None
