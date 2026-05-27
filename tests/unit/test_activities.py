"""
Unit tests for FastAPI endpoints using the AAA (Arrange-Act-Assert) pattern.
Tests individual endpoint behavior in isolation with controlled state.
"""
import pytest
from urllib.parse import quote
from fastapi.testclient import TestClient
from src.app import app


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self):
        """
        Test that GET /activities returns all activities with correct structure.
        
        AAA Pattern:
        - Arrange: Create a TestClient with the app
        - Act: Send GET request to /activities
        - Assert: Verify response status is 200 and all activities are returned
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9  # App has 9 pre-loaded activities
        assert "Chess Club" in activities
        assert "Debate Team" in activities
        
        # Verify activity structure
        chess = activities["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert isinstance(chess["participants"], list)


class TestRootEndpoint:
    """Tests for the GET / endpoint."""

    def test_root_endpoint_redirects_to_index(self):
        """
        Test that GET / redirects to /static/index.html.
        
        AAA Pattern:
        - Arrange: Create a TestClient with allow_redirects=False
        - Act: Send GET request to /
        - Assert: Verify redirect status (307)
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code in [307, 302, 301]  # Redirect status codes


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_with_valid_activity_and_email(self):
        """
        Test successful signup to an activity.
        
        AAA Pattern:
        - Arrange: Create a TestClient and select an activity
        - Act: Send POST request to signup endpoint with valid email
        - Assert: Verify response status is 200 and success message returned
        """
        # Arrange
        client = TestClient(app)
        email = "newstudent@example.com"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "signed up" in response.json()["message"].lower()

    def test_signup_duplicate_email_returns_400(self):
        """
        Test that signing up twice with same email returns 400 error.
        
        AAA Pattern:
        - Arrange: Create a TestClient and attempt first signup
        - Act: Try to signup again with same email
        - Assert: Verify response status is 400 (already registered)
        """
        # Arrange
        client = TestClient(app)
        email = "duplicate@example.com"
        activity_name = "Debate Team"
        
        # First signup - should succeed
        response1 = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Act - Try to signup again with same email
        response2 = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_to_nonexistent_activity_returns_404(self):
        """
        Test that signup to non-existent activity returns 404 error.
        
        AAA Pattern:
        - Arrange: Create a TestClient with non-existent activity name
        - Act: Send POST request to signup
        - Assert: Verify response status is 404
        """
        # Arrange
        client = TestClient(app)
        email = "student@example.com"
        nonexistent_activity = "Fake Activity"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_to_full_activity_returns_400(self):
        """
        Test that signup to full activity returns 400 error.
        
        AAA Pattern:
        - Arrange: Create an activity at full capacity and try to signup
        - Act: Send POST request to signup
        - Assert: Verify response status is 400 (capacity exceeded)
        """
        # Arrange
        client = TestClient(app)
        
        # Get all activities and find one we can fill up
        activities = client.get("/activities").json()
        
        # Use an activity with small capacity - find one to fill
        # Chess Club has max 12, let's try to fill it
        activity_name = "Chess Club"
        activity = activities[activity_name]
        current_count = len(activity["participants"])
        remaining_capacity = activity["max_participants"] - current_count
        
        # Fill the activity
        fill_emails = [f"filler{i}@test.com" for i in range(remaining_capacity)]
        for fill_email in fill_emails:
            response = client.post(
                f"/activities/{quote(activity_name)}/signup",
                params={"email": fill_email}
            )
            assert response.status_code == 200
        
        # Act - Try to signup when full
        overflow_email = "overflow@example.com"
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": overflow_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_with_valid_activity_and_registered_email(self):
        """
        Test successful unregister from an activity.
        
        AAA Pattern:
        - Arrange: Create a TestClient and signup first, then unregister
        - Act: Send POST request to unregister endpoint
        - Assert: Verify response status is 200 and success message returned
        """
        # Arrange
        client = TestClient(app)
        email = "temp@example.com"
        activity_name = "Art Club"
        
        # First signup
        signup_response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act - Unregister
        response = client.post(
            f"/activities/{quote(activity_name)}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

    def test_unregister_non_registered_student_returns_400(self):
        """
        Test that unregister fails if student is not registered.
        
        AAA Pattern:
        - Arrange: Create a TestClient with email not registered to activity
        - Act: Send POST request to unregister
        - Assert: Verify response status is 400
        """
        # Arrange
        client = TestClient(app)
        email = "notregistered@example.com"
        activity_name = "Basketball Team"
        
        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_from_nonexistent_activity_returns_404(self):
        """
        Test that unregister from non-existent activity returns 404 error.
        
        AAA Pattern:
        - Arrange: Create a TestClient with non-existent activity name
        - Act: Send POST request to unregister
        - Assert: Verify response status is 404
        """
        # Arrange
        client = TestClient(app)
        email = "student@example.com"
        nonexistent_activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
