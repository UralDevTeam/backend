"""Tests for utility functions."""
import pytest
from datetime import date, timedelta
from uuid import UUID
from uuid6 import uuid7

from src.domain.models import Team, EmployeeStatus
from src.utils.user import (
    build_full_name,
    build_short_name,
    build_team_lookup,
    collect_team_path,
    resolve_team,
    resolve_position,
    resolve_grade,
    resolve_experience,
    resolve_status,
    resolve_boss_id,
)


class MockEmployee:
    """Mock employee for testing."""
    def __init__(self, first_name=None, middle_name=None, last_name=None, team=None):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.team = team


def test_build_full_name_all_parts():
    """Test building full name with all parts."""
    employee = MockEmployee(first_name="John", middle_name="Michael", last_name="Doe")
    assert build_full_name(employee) == "Doe John Michael"


def test_build_full_name_no_middle():
    """Test building full name without middle name."""
    employee = MockEmployee(first_name="John", last_name="Doe")
    assert build_full_name(employee) == "Doe John"


def test_build_full_name_no_last():
    """Test building full name without last name."""
    employee = MockEmployee(first_name="John", middle_name="Michael")
    assert build_full_name(employee) == "John Michael"


def test_build_short_name():
    """Test building short name."""
    employee = MockEmployee(first_name="John", middle_name="Michael", last_name="Doe")
    assert build_short_name(employee) == "Doe J. M."


def test_build_short_name_no_middle():
    """Test building short name without middle name."""
    employee = MockEmployee(first_name="John", last_name="Doe")
    assert build_short_name(employee) == "Doe J."


def test_build_team_lookup():
    """Test building team lookup dictionary."""
    team1 = Team(id=uuid7(), name="Team 1", parent_id=None, leader_employee_id=uuid7())
    team2 = Team(id=uuid7(), name="Team 2", parent_id=team1.id, leader_employee_id=uuid7())
    lookup = build_team_lookup([team1, team2])
    assert len(lookup) == 2
    assert lookup[team1.id] == team1
    assert lookup[team2.id] == team2


def test_collect_team_path_single():
    """Test collecting team path for single team."""
    team = Team(id=uuid7(), name="Team", parent_id=None, leader_employee_id=uuid7())
    lookup = {team.id: team}
    path = collect_team_path(team, lookup)
    assert len(path) == 1
    assert path[0] == team


def test_collect_team_path_hierarchy():
    """Test collecting team path for team hierarchy."""
    root = Team(id=uuid7(), name="Root", parent_id=None, leader_employee_id=uuid7())
    child = Team(id=uuid7(), name="Child", parent_id=root.id, leader_employee_id=uuid7())
    grandchild = Team(id=uuid7(), name="Grandchild", parent_id=child.id, leader_employee_id=uuid7())
    lookup = {root.id: root, child.id: child, grandchild.id: grandchild}
    
    path = collect_team_path(grandchild, lookup)
    assert len(path) == 3
    assert path[0] == grandchild
    assert path[1] == child
    assert path[2] == root


def test_collect_team_path_none():
    """Test collecting team path with None team."""
    path = collect_team_path(None, {})
    assert path == []


def test_collect_team_path_circular_ref():
    """Test collecting team path with circular reference."""
    team1_id = uuid7()
    team2_id = uuid7()
    team1 = Team(id=team1_id, name="Team 1", parent_id=team2_id, leader_employee_id=uuid7())
    team2 = Team(id=team2_id, name="Team 2", parent_id=team1_id, leader_employee_id=uuid7())
    lookup = {team1_id: team1, team2_id: team2}
    
    # Should stop at first visit to avoid infinite loop
    path = collect_team_path(team1, lookup)
    assert len(path) == 2  # Should include both teams once


def test_resolve_team_with_team():
    """Test resolving team when employee has team."""
    team = Team(id=uuid7(), name="Team", parent_id=None, leader_employee_id=uuid7())
    employee = MockEmployee(team=team)
    lookup = {}
    result = resolve_team(employee, lookup)
    assert isinstance(result, list)
    assert team.id in lookup


def test_resolve_team_no_team():
    """Test resolving team when employee has no team."""
    employee = MockEmployee()
    lookup = {}
    result = resolve_team(employee, lookup)
    assert result == []


def test_resolve_position():
    """Test resolving position from employee."""
    class MockEmp:
        position = type('obj', (object,), {'title': 'Engineer'})()
    result = resolve_position(MockEmp())
    assert result == "Engineer"


def test_resolve_grade():
    """Test resolving grade from employee position."""
    class MockEmp:
        position = type('obj', (object,), {'title': 'Senior Engineer'})()
    result = resolve_grade(MockEmp())
    assert result == "Senior"


def test_resolve_grade_team_lead():
    """Test resolving grade for team lead."""
    class MockEmp:
        position = type('obj', (object,), {'title': 'Team Lead Developer'})()
    result = resolve_grade(MockEmp())
    assert result == "Team Lead"


def test_resolve_grade_no_match():
    """Test resolving grade with no matching keyword."""
    class MockEmp:
        position = type('obj', (object,), {'title': 'Software Engineer'})()
    result = resolve_grade(MockEmp())
    assert result == ""


def test_resolve_experience():
    """Test resolving work experience from employee."""
    class MockEmp:
        hire_date = date.today() - timedelta(days=365 * 5)
    days = resolve_experience(MockEmp())
    assert days >= 365 * 4  # At least 4 years
    assert days <= 365 * 6  # Less than 6 years


def test_resolve_status():
    """Test resolving employee status."""
    class StatusRecord:
        def __init__(self, status, ended_at=None, started_at=None):
            self.status = status
            self.ended_at = ended_at
            self.started_at = started_at
    
    class MockEmp:
        status_history = [StatusRecord(EmployeeStatus.ACTIVE)]
    
    status = resolve_status(MockEmp())
    assert status == EmployeeStatus.ACTIVE


def test_resolve_status_no_history():
    """Test resolving status with no history returns ACTIVE."""
    class MockEmp:
        status_history = []
    status = resolve_status(MockEmp())
    assert status == EmployeeStatus.ACTIVE


def test_resolve_boss_id():
    """Test resolving boss ID from team hierarchy."""
    leader_id = uuid7()
    employee_id = uuid7()
    team_obj = Team(id=uuid7(), name="Team", parent_id=None, leader_employee_id=leader_id)
    
    class MockEmp:
        id = employee_id
        team = team_obj
    
    lookup = {team_obj.id: team_obj}
    boss_id = resolve_boss_id(MockEmp(), lookup)
    assert boss_id == leader_id


def test_resolve_boss_id_no_team():
    """Test resolving boss ID with no team."""
    class MockEmp:
        id = uuid7()
    employee = MockEmp()
    boss_id = resolve_boss_id(employee, {})
    assert boss_id is None
