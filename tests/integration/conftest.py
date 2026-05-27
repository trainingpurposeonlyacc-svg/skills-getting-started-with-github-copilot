"""
Integration test configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def integration_client():
    """
    Provide a FastAPI TestClient for integration tests.
    This fixture creates a fresh client for each test to ensure isolation.
    """
    return TestClient(app)
