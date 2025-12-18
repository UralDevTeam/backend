from datetime import date
from typing import List, Dict, Set, Optional
from uuid import UUID

from src.domain.models import EmployeeStatus, Team


def build_full_name(employee) -> str:
    parts = [
        getattr(employee, "last_name", None),
        getattr(employee, "first_name", None),
        getattr(employee, "middle_name", None),
    ]
    return " ".join(part for part in parts if part).strip()


def build_short_name(employee) -> str:
    initials: List[str] = []
    if getattr(employee, "first_name", ""):
        initials.append(f"{employee.first_name[0]}.")
    if getattr(employee, "middle_name", ""):
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


def resolve_team(employee, lookup: Dict[UUID, Team]) -> List[str]:
    team = getattr(employee, "team", None)
    if not team:
        return []
    lookup.setdefault(team.id, team)

    path = list(reversed(collect_team_path(team, lookup)))
    names = [node.name for node in path if node.name]
    return names


def resolve_position(employee) -> str:
    position = getattr(employee, "position", None)
    return position.title if position and getattr(position, "title", None) else ""


def resolve_grade(employee) -> str:
    title = resolve_position(employee)
    if not title:
        return ""
    lower_title = title.lower()

    if lower_title.startswith("team lead"):
        return "Team Lead"
    for keyword in ("junior", "middle", "senior", "lead"):
        if lower_title.startswith(keyword):
            return keyword.capitalize()
    return ""


def resolve_experience(employee) -> int:
    hire_date = getattr(employee, "hire_date", None)
    if isinstance(hire_date, date):
        return max((date.today() - hire_date).days, 0)
    return 0


def resolve_status(employee) -> EmployeeStatus:
    history = getattr(employee, "status_history", []) or []
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


def resolve_boss_id(employee, lookup: Dict[UUID, Team]) -> Optional[UUID]:
    team = getattr(employee, "team", None)
    if not team:
        return None

    lookup.setdefault(team.id, team)

    path = collect_team_path(team, lookup)
    emp_id = employee.id

    for node in path:
        leader_id = node.leader_employee_id
        if leader_id and leader_id != emp_id:
            return leader_id

    return None
