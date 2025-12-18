"""Tests for DTOs."""
import pytest
from datetime import date
from uuid import UUID
from uuid6 import uuid7

from src.application.dto import (
    UserDTO,
    PingResponse,
    DetailResponse,
    UserUpdatePayload,
    AdminUserUpdatePayload,
    UserCreatePayload,
    EmployeeCreatePayload,
)
from src.domain.models import EmployeeStatus


class TestPingResponse:
    """Tests for PingResponse DTO."""
    
    def test_ping_response(self):
        """Test creating ping response."""
        response = PingResponse(ping="pong")
        assert response.ping == "pong"


class TestDetailResponse:
    """Tests for DetailResponse DTO."""
    
    def test_detail_response(self):
        """Test creating detail response."""
        response = DetailResponse(detail="Success")
        assert response.detail == "Success"


class TestEmployeeCreatePayload:
    """Tests for EmployeeCreatePayload DTO."""
    
    def test_employee_create_payload(self):
        """Test creating employee payload."""
        payload = EmployeeCreatePayload(
            first_name="John",
            middle_name="M",
            last_name="Doe",
            birth_date=date(1990, 1, 1),
            hire_date=date(2020, 1, 1),
            city="Moscow",
            email="john@example.com",
            phone="+79001234567",
            position="Developer",
            team="IT / Development"
        )
        assert payload.first_name == "John"
        assert payload.email == "john@example.com"


class TestUserUpdatePayload:
    """Tests for UserUpdatePayload DTO."""
    
    def test_user_update_payload(self):
        """Test creating user update payload."""
        payload = UserUpdatePayload(
            city="New York",
            phone="+12345678900"
        )
        assert payload.city == "New York"
        assert payload.phone == "+12345678900"


class TestAdminUserUpdatePayload:
    """Tests for AdminUserUpdatePayload DTO."""
    
    def test_admin_user_update_payload(self):
        """Test creating admin user update payload."""
        payload = AdminUserUpdatePayload(
            first_name="Jane",
            last_name="Doe"
        )
        assert payload.first_name == "Jane"
        assert payload.last_name == "Doe"
