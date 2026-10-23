from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


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
    assert response.json() == {"issues": []}
