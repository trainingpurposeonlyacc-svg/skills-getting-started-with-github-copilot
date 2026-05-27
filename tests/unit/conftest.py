"""
Unit test fixtures for activity business logic tests.
"""
import pytest


@pytest.fixture
def sample_activities():
    """
    Provide a sample activity database for unit testing.
    Mimics the structure used in src/app.py.
    """
    return {
        "Robotics Club": {
            "description": "Build and program robots",
            "schedule": "Monday, Wednesday 4:00 PM",
            "max_participants": 30,
            "participants": ["john@example.com", "jane@example.com"],
        },
        "Debate Team": {
            "description": "Practice debating skills",
            "schedule": "Tuesday, Thursday 3:30 PM",
            "max_participants": 20,
            "participants": ["bob@example.com"],
        },
        "Theater Club": {
            "description": "Perform theatrical productions",
            "schedule": "Saturday 2:00 PM",
            "max_participants": 2,
            "participants": ["alice@example.com", "charlie@example.com"],
        },
        "Chess Club": {
            "description": "Play competitive chess",
            "schedule": "Friday 4:00 PM",
            "max_participants": 1,
            "participants": [],
        },
    }


@pytest.fixture
def full_activity():
    """
    Provide an activity that is at full capacity.
    """
    return {
        "description": "Full activity",
        "schedule": "Monday 5:00 PM",
        "max_participants": 2,
        "participants": ["user1@example.com", "user2@example.com"],
    }


@pytest.fixture
def available_activity():
    """
    Provide an activity with available capacity.
    """
    return {
        "description": "Available activity",
        "schedule": "Tuesday 5:00 PM",
        "max_participants": 5,
        "participants": ["existing@example.com"],
    }
