"""Tests for authentication functions."""
import pytest
from datetime import datetime, timezone
from uuid import UUID
from unittest.mock import Mock, patch

from src.api.auth import (
    hash_password,
    verify_password,
    create_access_token,
)


class TestPasswordFunctions:
    """Tests for password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        hashed = hash_password("testpassword123")
        assert hashed is not None
        assert hashed != "testpassword123"
        assert len(hashed) > 20
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False
    
    def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2


class TestTokenCreation:
    """Tests for JWT token creation."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        subject = "user-id-123"
        issued_at = int(datetime.now(timezone.utc).timestamp())
        expires_delta = 3600
        
        token = create_access_token(subject, issued_at, expires_delta)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_create_access_token_different_subjects(self):
        """Test that different subjects create different tokens."""
        issued_at = int(datetime.now(timezone.utc).timestamp())
        expires_delta = 3600
        
        token1 = create_access_token("user1", issued_at, expires_delta)
        token2 = create_access_token("user2", issued_at, expires_delta)
        
        assert token1 != token2
