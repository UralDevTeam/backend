"""Integration tests for UserService.

This module contains comprehensive integration tests for the UserService,
testing all main functionality including CRUD operations, team management,
and user role handling.
"""
import pytest
from datetime import date
from uuid import UUID

from uuid6 import uuid7

from src.application.services.user import UserService, EmployeeCreationData
from src.application.dto import UserUpdatePayload, AdminUserUpdatePayload
from src.domain.models import User, Employee, Team, EmployeeStatus
from src.infrastructure.repositories.user import UserRepository
from src.infrastructure.repositories.employee import EmployeeRepository
from src.infrastructure.repositories.team import TeamRepository
from src.infrastructure.repositories.position import PositionRepository


@pytest.mark.integration
class TestUserServiceListUsers:
    """Tests for the list_users method."""

    @pytest.mark.asyncio
    async def test_list_users_empty(
        self,
        user_service: UserService,
    ):
        """Test listing users when database is empty."""
        users = await user_service.list_users()
        assert users == []

    @pytest.mark.asyncio
    async def test_list_users_single_employee(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test listing users with a single employee."""
        await session.commit()
        
        users = await user_service.list_users()
        
        assert len(users) == 1
        assert users[0].id == str(sample_employee.id)
        assert users[0].email == sample_employee.email
        assert users[0].fio == "Doe John Michael"
        assert users[0].isAdmin is False

    @pytest.mark.asyncio
    async def test_list_users_with_admin(
        self,
        user_service: UserService,
        admin_employee: Employee,
        admin_user: User,
        session,
    ):
        """Test listing users with admin privileges."""
        await session.commit()
        
        users = await user_service.list_users()
        
        assert len(users) == 1
        assert users[0].isAdmin is True

    @pytest.mark.asyncio
    async def test_list_users_sorted_by_last_name(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        sample_team: Team,
        sample_position,
        session,
    ):
        """Test that users are sorted by last name."""
        # Create employees with different last names
        employees_data = [
            {
                "id": uuid7(),
                "first_name": "Charlie",
                "middle_name": "C",
                "last_name": "Zebra",
                "email": "charlie@example.com",
                "birth_date": date(1990, 1, 1),
                "hire_date": date(2020, 1, 1),
                "position_id": sample_position.id,
                "team_id": sample_team.id,
            },
            {
                "id": uuid7(),
                "first_name": "Alice",
                "middle_name": "A",
                "last_name": "Alpha",
                "email": "alice@example.com",
                "birth_date": date(1990, 1, 1),
                "hire_date": date(2020, 1, 1),
                "position_id": sample_position.id,
                "team_id": sample_team.id,
            },
            {
                "id": uuid7(),
                "first_name": "Bob",
                "middle_name": "B",
                "last_name": "Beta",
                "email": "bob@example.com",
                "birth_date": date(1990, 1, 1),
                "hire_date": date(2020, 1, 1),
                "position_id": sample_position.id,
                "team_id": sample_team.id,
            },
        ]
        
        for emp_data in employees_data:
            await employee_repo.create(emp_data)
            await employee_repo.set_status(emp_data["id"], EmployeeStatus.ACTIVE)
        
        await session.commit()
        
        users = await user_service.list_users()
        
        assert len(users) == 3
        assert users[0].fio == "Alpha Alice A"
        assert users[1].fio == "Beta Bob B"
        assert users[2].fio == "Zebra Charlie C"


@pytest.mark.integration
class TestUserServiceGetUser:
    """Tests for the get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_existing(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test getting an existing user."""
        await session.commit()
        
        user_dto = await user_service.get_user(sample_employee.id)
        
        assert user_dto is not None
        assert user_dto.id == str(sample_employee.id)
        assert user_dto.email == sample_employee.email
        assert user_dto.fio == "Doe John Michael"

    @pytest.mark.asyncio
    async def test_get_user_nonexistent(
        self,
        user_service: UserService,
    ):
        """Test getting a non-existent user."""
        fake_id = uuid7()
        user_dto = await user_service.get_user(fake_id)
        
        assert user_dto is None

    @pytest.mark.asyncio
    async def test_get_user_with_boss(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        team_repo: TeamRepository,
        sample_position,
        sample_team: Team,
        session,
    ):
        """Test getting a user that has a boss."""
        # Create boss employee
        boss_id = uuid7()
        boss_data = {
            "id": boss_id,
            "first_name": "Boss",
            "middle_name": "The",
            "last_name": "Manager",
            "email": "boss@example.com",
            "birth_date": date(1980, 1, 1),
            "hire_date": date(2015, 1, 1),
            "position_id": sample_position.id,
            "team_id": sample_team.id,
        }
        boss = await employee_repo.create(boss_data)
        await employee_repo.set_status(boss_id, EmployeeStatus.ACTIVE)
        
        # Update team to set boss as leader
        await team_repo.update_leader(sample_team.id, boss_id)
        
        # Create subordinate employee in the same team
        subordinate_id = uuid7()
        subordinate_data = {
            "id": subordinate_id,
            "first_name": "Sub",
            "middle_name": "The",
            "last_name": "Ordinate",
            "email": "sub@example.com",
            "birth_date": date(1990, 1, 1),
            "hire_date": date(2020, 1, 1),
            "position_id": sample_position.id,
            "team_id": sample_team.id,
        }
        subordinate = await employee_repo.create(subordinate_data)
        await employee_repo.set_status(subordinate_id, EmployeeStatus.ACTIVE)
        
        await session.commit()
        
        user_dto = await user_service.get_user(subordinate_id)
        
        assert user_dto is not None
        assert user_dto.boss is not None
        assert user_dto.boss.id == str(boss_id)
        assert user_dto.boss.fullName == "Manager Boss The"


@pytest.mark.integration
class TestUserServiceGetMe:
    """Tests for the get_me method."""

    @pytest.mark.asyncio
    async def test_get_me_existing_user(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test getting current user's profile."""
        await session.commit()
        
        user_dto = await user_service.get_me(sample_user)
        
        assert user_dto is not None
        assert user_dto.id == str(sample_employee.id)
        assert user_dto.email == sample_user.email
        assert user_dto.isAdmin is False

    @pytest.mark.asyncio
    async def test_get_me_admin_user(
        self,
        user_service: UserService,
        admin_employee: Employee,
        admin_user: User,
        session,
    ):
        """Test getting admin user's profile."""
        await session.commit()
        
        user_dto = await user_service.get_me(admin_user)
        
        assert user_dto is not None
        assert user_dto.isAdmin is True

    @pytest.mark.asyncio
    async def test_get_me_no_employee_record(
        self,
        user_service: UserService,
        user_repo: UserRepository,
        session,
    ):
        """Test getting profile when user has no employee record."""
        # Create user without employee record
        orphan_user = User(
            id=uuid7(),
            email="orphan@example.com",
            password_hash="$2b$12$hash",
            role="user",
        )
        await user_repo.create(orphan_user)
        await session.commit()
        
        user_dto = await user_service.get_me(orphan_user)
        
        assert user_dto is None


@pytest.mark.integration
class TestUserServiceUpdateMe:
    """Tests for the update_me method."""

    @pytest.mark.asyncio
    async def test_update_me_basic_fields(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test updating user's own profile with basic fields."""
        await session.commit()
        
        payload = UserUpdatePayload(
            city="Saint Petersburg",
            phone="+79009876543",
            mattermost="@newhostname",
            tg="@newtelegram",
            about_me="Updated bio",
        )
        
        updated_user = await user_service.update_me(sample_user, payload)
        await session.commit()
        
        assert updated_user is not None
        assert updated_user.city == "Saint Petersburg"
        assert updated_user.phone == "+79009876543"
        assert updated_user.mattermost == "@newhostname"
        assert updated_user.tg == "@newtelegram"
        assert updated_user.aboutMe == "Updated bio"

    @pytest.mark.asyncio
    async def test_update_me_status(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        employee_repo: EmployeeRepository,
        session,
    ):
        """Test updating user's status."""
        await session.commit()
        
        payload = UserUpdatePayload(status=EmployeeStatus.VACATION)
        
        updated_user = await user_service.update_me(sample_user, payload)
        await session.commit()
        
        # Reload employee to check status was properly set
        reloaded_employee = await employee_repo.get_by_id(sample_employee.id)
        
        assert updated_user is not None
        assert reloaded_employee is not None
        # Check status from reloaded employee
        from src.domain.utils.user import resolve_status
        actual_status = resolve_status(reloaded_employee)
        assert actual_status == EmployeeStatus.VACATION

    @pytest.mark.asyncio
    async def test_update_me_birthdate_visibility(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test updating birth date visibility."""
        await session.commit()
        
        payload = UserUpdatePayload(is_birthyear_visible=False)
        
        updated_user = await user_service.update_me(sample_user, payload)
        await session.commit()
        
        assert updated_user is not None
        assert updated_user.isBirthyearVisible is False

    @pytest.mark.asyncio
    async def test_update_me_no_employee_record(
        self,
        user_service: UserService,
        user_repo: UserRepository,
        session,
    ):
        """Test updating profile when user has no employee record."""
        orphan_user = User(
            id=uuid7(),
            email="orphan@example.com",
            password_hash="$2b$12$hash",
            role="user",
        )
        await user_repo.create(orphan_user)
        await session.commit()
        
        payload = UserUpdatePayload(city="Moscow")
        
        result = await user_service.update_me(orphan_user, payload)
        
        assert result is None


@pytest.mark.integration
class TestUserServiceUpdateUser:
    """Tests for the update_user method (admin updates)."""

    @pytest.mark.asyncio
    async def test_update_user_basic_fields(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test admin updating user's basic fields."""
        await session.commit()
        
        payload = AdminUserUpdatePayload(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
        )
        
        updated_user = await user_service.update_user(sample_employee.id, payload)
        await session.commit()
        
        assert updated_user is not None
        assert updated_user.fio == "Smith Jane Michael"
        assert updated_user.email == "jane.smith@example.com"

    @pytest.mark.asyncio
    async def test_update_user_change_position(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test admin changing user's position."""
        await session.commit()
        
        payload = AdminUserUpdatePayload(position="Senior Software Engineer")
        
        updated_user = await user_service.update_user(sample_employee.id, payload)
        await session.commit()
        
        assert updated_user is not None
        assert updated_user.position == "Senior Software Engineer"

    @pytest.mark.asyncio
    async def test_update_user_promote_to_admin(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test promoting user to admin."""
        await session.commit()
        
        payload = AdminUserUpdatePayload(is_admin=True)
        
        updated_user = await user_service.update_user(sample_employee.id, payload)
        await session.commit()
        
        assert updated_user is not None
        assert updated_user.isAdmin is True

    @pytest.mark.asyncio
    async def test_update_user_demote_from_admin(
        self,
        user_service: UserService,
        admin_employee: Employee,
        admin_user: User,
        session,
    ):
        """Test demoting admin to regular user."""
        await session.commit()
        
        payload = AdminUserUpdatePayload(is_admin=False)
        
        updated_user = await user_service.update_user(admin_employee.id, payload)
        await session.commit()
        
        assert updated_user is not None
        assert updated_user.isAdmin is False

    @pytest.mark.asyncio
    async def test_update_user_change_team_existing(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        team_repo: TeamRepository,
        sample_team: Team,
        session,
    ):
        """Test changing user to an existing team."""
        await session.commit()
        
        # Use existing team name
        payload = AdminUserUpdatePayload(team=["Development"])
        
        updated_user = await user_service.update_user(sample_employee.id, payload)
        await session.commit()
        
        assert updated_user is not None
        assert "Development" in updated_user.team

    @pytest.mark.asyncio
    async def test_update_user_create_new_team(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test changing user to a new team (creates the team)."""
        await session.commit()
        
        payload = AdminUserUpdatePayload(team=["Development", "Backend Team"])
        
        updated_user = await user_service.update_user(sample_employee.id, payload)
        await session.commit()
        
        assert updated_user is not None
        assert "Backend Team" in updated_user.team

    @pytest.mark.asyncio
    async def test_update_user_nonexistent(
        self,
        user_service: UserService,
    ):
        """Test updating a non-existent user."""
        fake_id = uuid7()
        payload = AdminUserUpdatePayload(first_name="Test")
        
        result = await user_service.update_user(fake_id, payload)
        
        assert result is None


@pytest.mark.integration
class TestUserServiceCreateUser:
    """Tests for the create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_basic(
        self,
        user_service: UserService,
        admin_user: User,
        admin_employee: Employee,
        session,
    ):
        """Test creating a new user with basic information."""
        await session.commit()
        
        employee_data: EmployeeCreationData = {
            "first_name": "New",
            "middle_name": "Test",
            "last_name": "User",
            "birth_date": date(1995, 5, 15),
            "is_birthyear_visible": True,
            "hire_date": date(2023, 1, 1),
            "city": "Moscow",
            "phone": "+79005554433",
            "mattermost": "@newuser",
            "tg": "@newuser",
            "about_me": "New employee",
            "legal_entity": "Company LLC",
            "department": "IT",
            "position": "Junior Developer",
            "team": "Development",
        }
        
        new_user = await user_service.create_user(
            email="newuser@example.com",
            password_hash="$2b$12$newhash",
            role="user",
            employee_payload=employee_data,
            creator=admin_user,
        )
        await session.commit()
        
        assert new_user is not None
        assert new_user.email == "newuser@example.com"
        assert new_user.fio == "User New Test"
        assert new_user.position == "Junior Developer"
        assert new_user.isAdmin is False

    @pytest.mark.asyncio
    async def test_create_user_with_new_team(
        self,
        user_service: UserService,
        admin_user: User,
        admin_employee: Employee,
        session,
    ):
        """Test creating a user with a new team."""
        await session.commit()
        
        employee_data: EmployeeCreationData = {
            "first_name": "Team",
            "middle_name": "Lead",
            "last_name": "Person",
            "birth_date": date(1990, 1, 1),
            "is_birthyear_visible": True,
            "hire_date": date(2020, 1, 1),
            "city": None,
            "phone": None,
            "mattermost": None,
            "tg": None,
            "about_me": None,
            "legal_entity": None,
            "department": None,
            "position": "Team Lead",
            "team": "New Team",
        }
        
        new_user = await user_service.create_user(
            email="teamlead@example.com",
            password_hash="$2b$12$hash",
            role="user",
            employee_payload=employee_data,
            creator=admin_user,
        )
        await session.commit()
        
        assert new_user is not None
        assert "New Team" in new_user.team

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        user_service: UserService,
        admin_user: User,
        admin_employee: Employee,
        sample_user: User,
        session,
    ):
        """Test creating a user with duplicate email raises error."""
        await session.commit()
        
        employee_data: EmployeeCreationData = {
            "first_name": "Duplicate",
            "middle_name": "Email",
            "last_name": "User",
            "birth_date": date(1990, 1, 1),
            "is_birthyear_visible": True,
            "hire_date": date(2020, 1, 1),
            "city": None,
            "phone": None,
            "mattermost": None,
            "tg": None,
            "about_me": None,
            "legal_entity": None,
            "department": None,
            "position": "Developer",
            "team": "Development",
        }
        
        with pytest.raises(ValueError, match="User already registered"):
            await user_service.create_user(
                email="test@example.com",  # Same as sample_user
                password_hash="$2b$12$hash",
                role="user",
                employee_payload=employee_data,
                creator=admin_user,
            )

    @pytest.mark.asyncio
    async def test_create_admin_user(
        self,
        user_service: UserService,
        admin_user: User,
        admin_employee: Employee,
        session,
    ):
        """Test creating a user with admin role."""
        await session.commit()
        
        employee_data: EmployeeCreationData = {
            "first_name": "New",
            "middle_name": "Super",
            "last_name": "Admin",
            "birth_date": date(1985, 1, 1),
            "is_birthyear_visible": True,
            "hire_date": date(2019, 1, 1),
            "city": None,
            "phone": None,
            "mattermost": None,
            "tg": None,
            "about_me": None,
            "legal_entity": None,
            "department": None,
            "position": "System Administrator",
            "team": "IT",
        }
        
        new_admin = await user_service.create_user(
            email="newadmin@example.com",
            password_hash="$2b$12$hash",
            role="admin",
            employee_payload=employee_data,
            creator=admin_user,
        )
        await session.commit()
        
        assert new_admin is not None
        assert new_admin.isAdmin is True


@pytest.mark.integration
class TestUserServiceDeleteUser:
    """Tests for the delete_user method."""

    @pytest.mark.asyncio
    async def test_delete_regular_user(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        user_repo: UserRepository,
        sample_team: Team,
        sample_position,
        session,
    ):
        """Test deleting a regular user."""
        # Create a user who is not a team leader
        employee_id = uuid7()
        employee_data = {
            "id": employee_id,
            "first_name": "Delete",
            "middle_name": "Me",
            "last_name": "Please",
            "email": "delete@example.com",
            "birth_date": date(1990, 1, 1),
            "hire_date": date(2020, 1, 1),
            "position_id": sample_position.id,
            "team_id": sample_team.id,
        }
        await employee_repo.create(employee_data)
        
        user = User(
            id=uuid7(),
            email="delete@example.com",
            password_hash="$2b$12$hash",
            role="user",
        )
        await user_repo.create(user)
        await session.commit()
        
        # Delete the user
        await user_service.delete_user(employee_id)
        await session.commit()
        
        # Verify deletion
        deleted_employee = await employee_repo.get_by_id(employee_id)
        deleted_user = await user_repo.find_by_email("delete@example.com")
        
        assert deleted_employee is None
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_delete_team_leader_with_members(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        team_repo: TeamRepository,
        sample_position,
        session,
    ):
        """Test that deleting a team leader with members raises an error."""
        # Create team leader
        leader_id = uuid7()
        team = await team_repo.create(
            name="Test Team",
            leader_employee_id=leader_id,
            parent_id=None,
        )
        
        leader_data = {
            "id": leader_id,
            "first_name": "Team",
            "middle_name": "L",
            "last_name": "Leader",
            "email": "leader@example.com",
            "birth_date": date(1985, 1, 1),
            "hire_date": date(2015, 1, 1),
            "position_id": sample_position.id,
            "team_id": team.id,
        }
        await employee_repo.create(leader_data)
        
        # Create team member
        member_id = uuid7()
        member_data = {
            "id": member_id,
            "first_name": "Team",
            "middle_name": "M",
            "last_name": "Member",
            "email": "member@example.com",
            "birth_date": date(1990, 1, 1),
            "hire_date": date(2020, 1, 1),
            "position_id": sample_position.id,
            "team_id": team.id,
        }
        await employee_repo.create(member_data)
        await session.commit()
        
        # Attempt to delete team leader
        with pytest.raises(ValueError, match="лидер команды"):
            await user_service.delete_user(leader_id)

    @pytest.mark.asyncio
    async def test_delete_team_leader_alone_in_team(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        team_repo: TeamRepository,
        user_repo: UserRepository,
        sample_position,
        session,
    ):
        """Test deleting a team leader who is alone in their team."""
        # Create team leader
        leader_id = uuid7()
        team = await team_repo.create(
            name="Solo Team",
            leader_employee_id=leader_id,
            parent_id=None,
        )
        
        leader_data = {
            "id": leader_id,
            "first_name": "Solo",
            "middle_name": "L",
            "last_name": "Leader",
            "email": "solo@example.com",
            "birth_date": date(1985, 1, 1),
            "hire_date": date(2015, 1, 1),
            "position_id": sample_position.id,
            "team_id": team.id,
        }
        await employee_repo.create(leader_data)
        
        user = User(
            id=uuid7(),
            email="solo@example.com",
            password_hash="$2b$12$hash",
            role="user",
        )
        await user_repo.create(user)
        await session.commit()
        
        # Delete the solo team leader
        await user_service.delete_user(leader_id)
        await session.commit()
        
        # Verify deletion
        deleted_employee = await employee_repo.get_by_id(leader_id)
        deleted_user = await user_repo.find_by_email("solo@example.com")
        
        assert deleted_employee is None
        assert deleted_user is None


@pytest.mark.integration
class TestUserServiceResolveTeamId:
    """Tests for the _resolve_team_id method (team hierarchy handling)."""

    @pytest.mark.asyncio
    async def test_resolve_team_id_existing_hierarchy(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        team_repo: TeamRepository,
        sample_position,
        session,
    ):
        """Test resolving team ID with existing hierarchy."""
        # Create team hierarchy: Parent -> Child
        parent_id = uuid7()
        parent_leader_id = uuid7()
        
        parent_leader_data = {
            "id": parent_leader_id,
            "first_name": "Parent",
            "middle_name": "L",
            "last_name": "Leader",
            "email": "parent@example.com",
            "birth_date": date(1980, 1, 1),
            "hire_date": date(2010, 1, 1),
            "position_id": sample_position.id,
            "team_id": parent_id,  # Temporary, will be updated
        }
        
        parent_team = await team_repo.create(
            name="Parent Team",
            leader_employee_id=parent_leader_id,
            parent_id=None,
        )
        
        # Update employee with correct team
        parent_leader_data["team_id"] = parent_team.id
        parent_leader = await employee_repo.create(parent_leader_data)
        
        child_team = await team_repo.create(
            name="Child Team",
            leader_employee_id=parent_leader_id,
            parent_id=parent_team.id,
        )
        
        await session.commit()
        
        # Resolve team ID
        resolved_id = await user_service._resolve_team_id(
            parent_leader,
            ["Parent Team", "Child Team"]
        )
        
        assert resolved_id == child_team.id

    @pytest.mark.asyncio
    async def test_resolve_team_id_create_new_leaf(
        self,
        user_service: UserService,
        employee_repo: EmployeeRepository,
        team_repo: TeamRepository,
        sample_employee: Employee,
        sample_team: Team,
        session,
    ):
        """Test resolving team ID creates new leaf team."""
        await session.commit()
        
        # Resolve with existing parent and new child
        resolved_id = await user_service._resolve_team_id(
            sample_employee,
            ["Development", "New Sub Team"]
        )
        await session.commit()
        
        # Verify new team was created
        new_team = await team_repo.find_by_name("New Sub Team", parent_id=sample_team.id)
        
        assert new_team is not None
        assert resolved_id == new_team.id
        assert new_team.parent_id == sample_team.id

    @pytest.mark.asyncio
    async def test_resolve_team_id_invalid_middle_team(
        self,
        user_service: UserService,
        sample_employee: Employee,
        sample_team: Team,
        session,
    ):
        """Test that invalid middle team in hierarchy raises error."""
        await session.commit()
        
        # Try to resolve with non-existent middle team
        with pytest.raises(ValueError, match="not found"):
            await user_service._resolve_team_id(
                sample_employee,
                ["Development", "Non Existent", "Leaf Team"]
            )

    @pytest.mark.asyncio
    async def test_resolve_team_id_empty_list(
        self,
        user_service: UserService,
        sample_employee: Employee,
        session,
    ):
        """Test that empty team list raises error."""
        await session.commit()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            await user_service._resolve_team_id(sample_employee, [])

    @pytest.mark.asyncio
    async def test_resolve_team_id_whitespace_team_name(
        self,
        user_service: UserService,
        sample_employee: Employee,
        session,
    ):
        """Test that whitespace-only team name raises error."""
        await session.commit()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            await user_service._resolve_team_id(sample_employee, ["   "])
