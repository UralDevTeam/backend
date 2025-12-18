"""Tests for configuration settings."""
import pytest
from src.config import settings


class TestSettings:
    """Tests for configuration settings."""
    
    def test_settings_exist(self):
        """Test that settings object exists."""
        assert settings is not None
    
    def test_database_url_exists(self):
        """Test that database URL setting exists."""
        assert hasattr(settings, 'postgres')
    
    def test_ad_settings_exist(self):
        """Test that AD settings exist."""
        assert hasattr(settings, 'ad')
