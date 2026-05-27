"""
Shared test configuration and fixtures for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Provide a FastAPI TestClient for making HTTP requests to the app.
    This fixture is used by integration tests.
    """
    return TestClient(app)
