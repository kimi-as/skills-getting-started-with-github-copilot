"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestGetActivities:
    """Test cases for retrieving activities"""

    def test_get_activities_success(self):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) > 0

    def test_get_activities_contains_required_fields(self):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_has_initial_participants(self):
        """Test that some activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Test cases for signing up for activities"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Tennis" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "test.student@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Art Studio"]["participants"])
        
        # Sign up
        response = client.post(f"/activities/Art Studio/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Art Studio"]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()["Art Studio"]["participants"]

    def test_signup_duplicate_email_fails(self):
        """Test that signing up with an existing email fails"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Non Existent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestUnregister:
    """Test cases for unregistering from activities"""

    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        # First sign up
        email = "unregister.test@mergington.edu"
        client.post(f"/activities/Science Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Science Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove.me@mergington.edu"
        activity = "Debate Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify they're in the list
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify they're removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_unregister_not_signed_up_fails(self):
        """Test that unregistering someone not signed up fails"""
        response = client.post(
            "/activities/Basketball/unregister?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from a non-existent activity fails"""
        response = client.post(
            "/activities/Fake Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRoot:
    """Test cases for the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestEdgeCases:
    """Test cases for edge cases and error handling"""

    def test_signup_with_spaces_in_activity_name(self):
        """Test signup with activity names that have spaces"""
        response = client.post(
            "/activities/Programming Class/signup?email=programmer@mergington.edu"
        )
        assert response.status_code == 200

    def test_multiple_signups_same_activity(self):
        """Test that multiple different students can sign up for the same activity"""
        email1 = "student1.multi@mergington.edu"
        email2 = "student2.multi@mergington.edu"
        activity = "Drama Club"
        
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert email1 in participants
        assert email2 in participants

    def test_signup_and_unregister_workflow(self):
        """Test complete workflow of signing up and unregistering"""
        email = "workflow.test@mergington.edu"
        activity = "Art Studio"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify added
        response = client.get("/activities")
        after_signup = len(response.json()[activity]["participants"])
        assert after_signup == initial_count + 1
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        after_unregister = len(response.json()[activity]["participants"])
        assert after_unregister == initial_count
