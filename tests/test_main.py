from fastapi.testclient import TestClient
from main import app
import copy
import pytest
import main

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_issues():
    original = copy.deepcopy(main.issues)
    yield
    main.issues[:] = original


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
    # 3. Assert response body == {"issues": issues}
    returned_json = response.json()["issues"]
    assert len(returned_json) == 3
    assert [issue["id"] for issue in returned_json] == [101, 102, 103]


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
    assert response.json() == {"detail": "Issue not found."}


def test_get_issue_invalid_id():
    # GET /issues/abc
    response = client.get("/issues/abc")
    # Assert status == 422
    assert response.status_code == 422

    body = response.json()

    assert body["detail"][0]["loc"] == ["path", "issue_id"]


def test_create_issue_success():
    response = client.post("/issues", json={"title": "Battery issue", "status": "open"})

    assert response.status_code == 201

    body = response.json()
    assert body["title"] == "Battery issue"
    assert body["status"] == "open"
    assert body["id"] == 104


def test_create_issue_default_status():
    response = client.post("/issues", json={"title": "Battery issue"})
    assert response.status_code == 201

    # check total issue list
    issues_total = client.get("/issues")
    assert issues_total.status_code == 200
    assert len(issues_total.json()["issues"]) == 4

    body = response.json()
    assert body["title"] == "Battery issue"
    assert body["status"] == "open"
    assert body["id"] == 104


def test_create_issue_missing_title():
    before_count = len(main.issues)
    response = client.post("/issues", json={"status": "open"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]

    # check that the total issue list should not change
    issues_total = client.get("/issues")
    assert len(issues_total.json()["issues"]) == before_count


def test_create_issue_empty_title():
    before_count = len(main.issues)
    response = client.post("/issues", json={"title": ""})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]

    # check that the total issue list should not change
    issues_total = client.get("/issues")
    assert len(issues_total.json()["issues"]) == before_count


def test_create_issue_invalid_status():
    before_count = len(main.issues)
    response = client.post(
        "/issues", json={"title": "Battery issue", "status": "pending"}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "status"]

    # check that the total issue list should not change
    issues_total = client.get("/issues")
    assert len(issues_total.json()["issues"]) == before_count


def test_create_issue_data_persistence():
    response = client.post("/issues", json={"title": "Battery issue"})
    assert response.status_code == 201
    body = response.json()
    issue_id = body["id"]

    response = client.get(f"/issues/{issue_id}")
    assert response.status_code == 200

    assert response.json() == {"id": 104, "title": "Battery issue", "status": "open"}
