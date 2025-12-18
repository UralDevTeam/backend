"""API endpoint tests."""
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestPingEndpoint:
    """Tests for the ping endpoint."""
    
    def test_ping_returns_pong(self, client):
        """Test that ping endpoint returns pong."""
        response = client.get("/api/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}
