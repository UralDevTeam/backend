"""Tests for AD import service."""
import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID

from src.application.services.ad_import import AdImportService
from src.infrastructure.repositories import EmployeeRepository, PositionRepository, TeamRepository
from src.domain.models import Team, Position


@pytest.mark.asyncio
class TestAdImportService:
    """Tests for AdImportService."""
    
    async def test_parse_date_with_valid_date(self):
        """Test parsing a valid date."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._parse_date("2020-01-15")
        assert result == date(2020, 1, 15)
    
    async def test_parse_date_with_none(self):
        """Test parsing None returns None."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._parse_date(None)
        assert result is None
    
    async def test_parse_date_with_date_object(self):
        """Test parsing a date object returns the same date."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        test_date = date(2020, 1, 15)
        result = service._parse_date(test_date)
        assert result == test_date
    
    async def test_first_attr_with_list(self):
        """Test extracting first attribute from a list."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._first_attr({"key": ["value1", "value2"]}, "key")
        assert result == "value1"
    
    async def test_first_attr_with_single_value(self):
        """Test extracting attribute that is not a list."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._first_attr({"key": "value"}, "key")
        assert result == "value"
    
    async def test_first_attr_missing_key(self):
        """Test extracting attribute that doesn't exist."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._first_attr({"other": "value"}, "key")
        assert result is None
    
    async def test_normalize_city_with_valid_string(self):
        """Test normalizing a valid city name."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._normalize_city("  Moscow  ")
        assert result == "Moscow"
    
    async def test_normalize_city_with_none(self):
        """Test normalizing None returns None."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._normalize_city(None)
        assert result is None
    
    async def test_normalize_city_with_empty_string(self):
        """Test normalizing empty string returns None."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        result = service._normalize_city("   ")
        assert result is None
    
    async def test_is_service_account_with_service_ou(self):
        """Test identifying service account by OU."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        entry = {
            "dn": "CN=Service Account,OU=Service,DC=example,DC=com",
            "attributes": {}
        }
        
        result = service._is_service_account(entry)
        assert result is True
    
    async def test_is_service_account_with_regular_user(self):
        """Test identifying regular user account."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        entry = {
            "dn": "CN=John Doe,OU=Users,DC=example,DC=com",
            "attributes": {}
        }
        
        result = service._is_service_account(entry)
        assert result is False
    
    async def test_build_manager_lookup(self):
        """Test building manager lookup dictionary."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        entries = [
            {
                "dn": "CN=John Doe,OU=Users,DC=example,DC=com",
                "attributes": {"objectGUID": "guid-123"}
            },
            {
                "dn": "CN=Jane Smith,OU=Users,DC=example,DC=com",
                "attributes": {"objectGUID": ["guid-456"]}
            }
        ]
        
        result = service._build_manager_lookup(entries)
        assert result["cn=john doe,ou=users,dc=example,dc=com"] == "guid-123"
        assert result["cn=jane smith,ou=users,dc=example,dc=com"] == "guid-456"
    
    async def test_map_entry_with_valid_user(self):
        """Test mapping a valid AD entry to employee data."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        entry = {
            "dn": "CN=John Doe,OU=Users,DC=example,DC=com",
            "attributes": {
                "objectGUID": "guid-123",
                "mail": "john.doe@example.com",
                "givenName": "John",
                "sn": "Doe",
                "title": "Software Engineer",
                "department": "IT",
                "company": "Example Corp",
                "l": "Moscow",
                "telephoneNumber": "+79001234567"
            }
        }
        
        result = service._map_entry(entry, {})
        
        assert result is not None
        assert result["object_id"] == "guid-123"
        assert result["email"] == "john.doe@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["position"] == "Software Engineer"
        assert result["department"] == "IT"
        assert result["legal_entity"] == "Example Corp"
        assert result["city"] == "Moscow"
        assert result["phone"] == "+79001234567"
    
    async def test_map_entry_with_missing_required_fields(self):
        """Test mapping entry with missing required fields returns None."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        entry = {
            "dn": "CN=Invalid User,OU=Users,DC=example,DC=com",
            "attributes": {}
        }
        
        result = service._map_entry(entry, {})
        assert result is None
    
    async def test_map_entry_with_service_account(self):
        """Test mapping service account returns None."""
        service = AdImportService(
            Mock(spec=EmployeeRepository),
            Mock(spec=PositionRepository),
            Mock(spec=TeamRepository),
        )
        
        entry = {
            "dn": "CN=Service Account,OU=Service,DC=example,DC=com",
            "attributes": {
                "objectGUID": "guid-123",
                "mail": "service@example.com"
            }
        }
        
        result = service._map_entry(entry, {})
        assert result is None
