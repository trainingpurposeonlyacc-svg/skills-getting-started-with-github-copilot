"""
Integration tests for the FastAPI app using the AAA (Arrange-Act-Assert) pattern.
Tests complex workflows and interactions between endpoints.
"""
import pytest
from urllib.parse import quote
from fastapi.testclient import TestClient
from src.app import app


class TestActivitiesWorkflow:
    """Integration tests for multi-step activity workflows."""

    def test_signup_then_unregister_then_signup_again(self):
        """
        Test a complete workflow: signup, unregister, then signup again.
        
        AAA Pattern:
        - Arrange: Create a TestClient and prepare email/activity
        - Act: Signup, unregister, signup again in sequence
        - Assert: Verify each step succeeds with expected status codes
        """
        # Arrange
        client = TestClient(app)
        email = "workflow@example.com"
        activity = "Programming Class"
        
        # Act & Assert - Step 1: Signup
        response1 = client.post(
            f"/activities/{quote(activity)}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert "signed up" in response1.json()["message"].lower()
        
        # Act & Assert - Step 2: Unregister
        response2 = client.post(
            f"/activities/{quote(activity)}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        assert "removed" in response2.json()["message"].lower()
        
        # Act & Assert - Step 3: Signup again (should succeed)
        response3 = client.post(
            f"/activities/{quote(activity)}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        assert "signed up" in response3.json()["message"].lower()

    def test_multiple_students_signup_to_activity(self):
        """
        Test that multiple students can signup to the same activity.
        
        AAA Pattern:
        - Arrange: Create a TestClient and prepare multiple emails
        - Act: Have multiple students signup to same activity
        - Assert: Verify all signups succeed
        """
        # Arrange
        client = TestClient(app)
        emails = [
            "student1@example.com",
            "student2@example.com",
            "student3@example.com",
        ]
        activity = "Swimming Club"
        
        # Act
        responses = []
        for email in emails:
            response = client.post(
                f"/activities/{quote(activity)}/signup",
                params={"email": email}
            )
            responses.append(response)
        
        # Assert
        for response in responses:
            assert response.status_code == 200
            assert "signed up" in response.json()["message"].lower()

    def test_verify_participants_list_updated_after_signup(self):
        """
        Test that participants list is updated after successful signup.
        
        AAA Pattern:
        - Arrange: Get initial participants count
        - Act: Signup a new student
        - Assert: Verify participants count increased by 1
        """
        # Arrange
        client = TestClient(app)
        email = "newparticipant@example.com"
        activity = "Math Olympiad"
        
        # Get initial state
        activities_before = client.get("/activities").json()
        participants_before = len(activities_before[activity]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{quote(activity)}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Assert
        activities_after = client.get("/activities").json()
        participants_after = len(activities_after[activity]["participants"])
        assert participants_after == participants_before + 1
        assert email in activities_after[activity]["participants"]

    def test_verify_participants_list_updated_after_unregister(self):
        """
        Test that participants list is updated after successful unregister.
        
        AAA Pattern:
        - Arrange: Signup a student, get initial participants count
        - Act: Unregister the student
        - Assert: Verify participants count decreased by 1
        """
        # Arrange
        client = TestClient(app)
        email = "temporary@example.com"
        activity = "Drama Workshop"
        
        # Signup first
        response = client.post(
            f"/activities/{quote(activity)}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Get participants count after signup
        activities_mid = client.get("/activities").json()
        participants_before_unregister = len(activities_mid[activity]["participants"])
        
        # Act
        unregister_response = client.post(
            f"/activities/{quote(activity)}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Assert
        activities_after = client.get("/activities").json()
        participants_after = len(activities_after[activity]["participants"])
        assert participants_after == participants_before_unregister - 1
        assert email not in activities_after[activity]["participants"]


class TestErrorRecovery:
    """Integration tests for error handling and recovery."""

    def test_recover_from_invalid_activity_then_valid_activity(self):
        """
        Test that user can recover from signup error to invalid activity.
        
        AAA Pattern:
        - Arrange: Create a TestClient
        - Act: Try signup to invalid activity, then valid activity
        - Assert: First fails (404), second succeeds (200)
        """
        # Arrange
        client = TestClient(app)
        email = "recovery@example.com"
        
        # Act & Assert - Invalid activity
        response1 = client.post(
            f"/activities/{quote('Invalid Activity')}/signup",
            params={"email": email}
        )
        assert response1.status_code == 404
        
        # Act & Assert - Valid activity (recovery)
        response2 = client.post(
            f"/activities/{quote('Gym Class')}/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        assert "signed up" in response2.json()["message"].lower()

    def test_capacity_limit_enforcement(self):
        """
        Test that activity capacity limits are properly enforced.
        
        AAA Pattern:
        - Arrange: Identify activity with specific capacity
        - Act: Fill activity to capacity, then try to add one more
        - Assert: Last signup fails with 400 status
        """
        # Arrange
        client = TestClient(app)
        activity = "Basketball Team"  # Max 15 participants
        
        # Get initial state
        activities = client.get("/activities").json()
        initial_count = len(activities[activity]["participants"])
        max_capacity = activities[activity]["max_participants"]
        
        # If not at capacity, fill it first
        students_to_add = max_capacity - initial_count
        emails_added = []
        for i in range(students_to_add):
            email = f"filler{i}@example.com"
            emails_added.append(email)
            response = client.post(
                f"/activities/{quote(activity)}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Act - Try to add one more (should fail)
        overflow_email = "overflow@example.com"
        response = client.post(
            f"/activities/{quote(activity)}/signup",
            params={"email": overflow_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()

    def test_activities_remain_accessible_after_errors(self):
        """
        Test that activities endpoint remains accessible after signup errors.
        
        AAA Pattern:
        - Arrange: Create a TestClient
        - Act: Trigger signup error, then request activities
        - Assert: Activities endpoint returns 200 with valid data
        """
        # Arrange
        client = TestClient(app)
        
        # Act - Trigger error (invalid activity)
        error_response = client.post(
            f"/activities/{quote('Invalid Activity')}/signup",
            params={"email": "test@example.com"}
        )
        assert error_response.status_code == 404
        
        # Act - Get activities after error
        activities_response = client.get("/activities")
        
        # Assert
        assert activities_response.status_code == 200
        activities = activities_response.json()
        assert len(activities) > 0
        assert isinstance(activities, dict)


class TestActivityData:
    """Integration tests for activity data consistency."""

    def test_all_activities_have_required_fields(self):
        """
        Test that all activities have required fields in the response.
        
        AAA Pattern:
        - Arrange: Request all activities
        - Act: Retrieve activities data
        - Assert: Verify each activity has all required fields
        """
        # Arrange
        client = TestClient(app)
        required_fields = {
            "description",
            "schedule",
            "max_participants",
            "participants",
        }
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity '{activity_name}' missing required fields"
            
            # Verify field types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_participants_are_unique_in_activity(self):
        """
        Test that participants list contains unique emails.
        
        AAA Pattern:
        - Arrange: Request all activities
        - Act: Check participants in each activity
        - Assert: Verify no duplicate emails in any activity's participants
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            unique_participants = set(participants)
            assert len(participants) == len(unique_participants), \
                f"Activity '{activity_name}' has duplicate participants"
