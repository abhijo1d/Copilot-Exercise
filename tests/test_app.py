import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def test_root_redirect(client):
    """Test that the root path redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test fetching all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Basketball" in activities
    
    # Test structure of an activity
    chess = activities["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)


def test_signup_for_activity(client):
    """Test signing up for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert "test@mergington.edu" in result["message"]
    assert "Chess Club" in result["message"]
    
    # Verify the participant was added
    activities = client.get("/activities").json()
    assert "test@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_duplicate_student(client):
    """Test that a student can't sign up twice for the same activity"""
    # First signup
    response1 = client.post(
        "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
    )
    assert response1.status_code == 200
    
    # Try to sign up again
    response2 = client.post(
        "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
    )
    assert response2.status_code == 400
    assert "already signed up" in response2.json()["detail"]


def test_signup_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_unregister_from_activity(client):
    """Test unregistering from an activity"""
    # First, sign up
    client.post("/activities/Tennis%20Club/signup?email=tennis@mergington.edu")
    
    # Verify participant was added
    activities = client.get("/activities").json()
    assert "tennis@mergington.edu" in activities["Tennis Club"]["participants"]
    
    # Now unregister
    response = client.post(
        "/activities/Tennis%20Club/unregister?email=tennis@mergington.edu"
    )
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    
    # Verify participant was removed
    activities = client.get("/activities").json()
    assert "tennis@mergington.edu" not in activities["Tennis Club"]["participants"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404


def test_unregister_student_not_registered(client):
    """Test unregistering a student who isn't registered"""
    response = client.post(
        "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_activities_have_initial_participants(client):
    """Test that activities have initial participants"""
    activities = client.get("/activities").json()
    
    # Verify some activities have participants
    assert len(activities["Chess Club"]["participants"]) > 0
    assert "michael@mergington.edu" in activities["Chess Club"]["participants"]


def test_max_participants_constraint(client):
    """Test that max_participants is enforced"""
    response = client.get("/activities")
    activities = response.json()
    
    for activity_name, details in activities.items():
        # Check that participants don't exceed max
        assert len(details["participants"]) <= details["max_participants"]
