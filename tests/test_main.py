from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
issues = [
    {"id": 101, "title": "Login fails", "status": "open"},
    {"id": 102, "title": "App crashes", "status": "closed"},
    {"id": 103, "title": "Slow loading", "status": "open"},
]


def test_health_check():
    # 1. Send a GET request to /health
    response = client.get("/health")
    # 2. Assert status code == 200
    assert response.status_code == 200
    # 3. Assert response body == {"status": "ok"}
    assert response.json() == {"status": "ok"}


def test_get_issues():
    # 1. Send a GET request to /issues
    response = client.get("/issues")
    # 2. Assert status code == 200
    assert response.status_code == 200
    # 3. Assert response body == {"issues": []}
    assert response.json() == {"issues": issues}


def test_get_issue_success():
    # GET /issues/101
    response = client.get("/issues/101")
    # Assert status == 200
    assert response.status_code == 200
    # Assert ID, title, and status
    assert response.json() == {"id": 101, "title": "Login fails", "status": "open"}


def test_get_issue_not_found():
    # GET /issues/999
    response = client.get("/issues/999")
    # Assert status == 404
    assert response.status_code == 404
    # Assert error response
    assert response.json() == {"detail": "issue not found"}


def test_get_issue_invalid_id():
    # GET /issues/abc
    response = client.get("/issues/abc")
    # Assert status == 422
    assert response.status_code == 422
