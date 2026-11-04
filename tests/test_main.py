from fastapi.testclient import TestClient
from main import app
from database import get_session
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from models import Issue


# use SQLite in-memory mode
@pytest.fixture(name="session")
def session():
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    try:
        # Create the database tables
        SQLModel.metadata.create_all(test_engine)

        with Session(test_engine) as session:
            yield session
    finally:
        # 4: Dispose of test_engine after the Session closes
        test_engine.dispose()


# client fixture
@pytest.fixture(name="client")
def client(session: Session):
    # Create get_session_override()
    # that yields the test session
    def get_session_override():
        return session

    # Set app.dependency_overrides[get_session], reference to the overrided function
    app.dependency_overrides[get_session] = get_session_override

    try:
        # Create and yield TestClient(app)
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clear dependency overrides after testing
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def existing_issue(session: Session):
    """Fixture for creating an issue into database for testing"""
    issue = Issue(id=101, title="Login fails", status="open")
    session.add(issue)
    session.commit()
    session.refresh(issue)
    return issue


def test_health_check(client: TestClient):
    # 1. Send a GET request to /health
    response = client.get("/health")
    # 2. Assert status code == 200
    assert response.status_code == 200
    # 3. Assert response body == {"status": "ok"}
    assert response.json() == {"status": "ok"}


def test_get_issues(client: TestClient, existing_issue: Issue):
    # Send GET /issues using client
    response = client.get("/issues")

    # Assert response.status_code == 200
    assert response.status_code == 200

    # Verify:
    # - Exactly one Issue is returned
    # - Its ID is 101
    # - Its title is "Login fails"
    # - Its status is "open"
    returned_issues = response.json()["issues"]
    assert len(returned_issues) == 1

    first_issue = returned_issues[0]

    assert first_issue["id"] == 101
    assert first_issue["title"] == "Login fails"
    assert first_issue["status"] == "open"


def test_get_issue_success(client: TestClient, existing_issue: Issue):
    response = client.get("/issues/101")

    assert response.status_code == 200

    assert response.json() == {"id": 101, "title": "Login fails", "status": "open"}


def test_get_issue_not_found(client: TestClient):
    response = client.get("/issues/999")
    assert response.status_code == 404

    assert response.json() == {"detail": "Issue not found."}


def test_get_issue_invalid_id(client: TestClient):
    # GET /issues/abc
    response = client.get("/issues/abc")
    # Assert status == 422
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["loc"] == ["path", "issue_id"]


def test_create_issue_success(client: TestClient):
    response = client.post("/issues", json={"title": "Battery issue", "status": "open"})

    assert response.status_code == 201

    created_issue = response.json()
    assert created_issue["title"] == "Battery issue"
    assert created_issue["status"] == "open"
    issue_id = created_issue["id"]
    assert isinstance(issue_id, int)
    assert issue_id > 0


def test_create_issue_default_status(client: TestClient):
    response = client.post("/issues", json={"title": "Battery issue"})
    assert response.status_code == 201

    # check total issue list
    issues_total = client.get("/issues")
    assert issues_total.status_code == 200
    assert len(issues_total.json()["issues"]) == 1
    created_issue = response.json()
    assert created_issue["title"] == "Battery issue"
    assert created_issue["status"] == "open"
    issue_id = created_issue["id"]
    assert isinstance(issue_id, int)
    assert issue_id > 0


def test_create_issue_missing_title(client: TestClient, session: Session):
    response = client.post("/issues", json={"status": "open"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]

    # Verify that no record was inserted into the database
    statement = select(Issue)
    results = session.exec(statement)
    issues_list = results.all()
    assert len(issues_list) == 0


def test_create_issue_empty_title(client: TestClient, session: Session):
    response = client.post("/issues", json={"title": ""})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]

    # Verify that no record was inserted into the database
    statement = select(Issue)
    results = session.exec(statement)
    issues_list = results.all()
    assert len(issues_list) == 0


def test_create_issue_invalid_status(client: TestClient, session: Session):
    response = client.post(
        "/issues", json={"title": "Battery issue", "status": "pending"}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "status"]

    # Verify that no record was inserted into the database
    statement = select(Issue)
    results = session.exec(statement)
    issues_list = results.all()
    assert len(issues_list) == 0


def test_create_issue_data_persistence(client: TestClient):
    response = client.post("/issues", json={"title": "Battery issue"})
    assert response.status_code == 201
    body = response.json()
    issue_id = body["id"]

    response = client.get(f"/issues/{issue_id}")
    assert response.status_code == 200

    assert response.json() == {
        "id": issue_id,
        "title": "Battery issue",
        "status": "open",
    }


def test_update_issue_status(client: TestClient, existing_issue: Issue):
    response = client.patch("/issues/101", json={"status": "closed"})
    assert response.status_code == 200
    assert response.json() == {
        "id": 101,
        "title": "Login fails",
        "status": "closed",
    }


def test_update_issue_title(client: TestClient, existing_issue: Issue):
    response = client.patch(
        "/issues/101", json={"title": "Login fails after password reset"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 101,
        "title": "Login fails after password reset",
        "status": "open",
    }


def test_update_issue_not_found(client: TestClient):
    response = client.patch("/issues/999", json={"status": "closed"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Issue not found"}


def test_update_issue_invalid_status(
    client: TestClient, session: Session, existing_issue: Issue
):
    response = client.patch("/issues/101", json={"status": "pending"})

    assert response.status_code == 422
    # Assert error location ["body", "status"]
    assert response.json()["detail"][0]["loc"] == ["body", "status"]

    # check the issue still remain unchanged
    issue = session.get(Issue, 101)
    session.refresh(issue)
    assert issue.title == "Login fails"
    assert issue.status == "open"


def test_update_issue_empty_title(
    client: TestClient, session: Session, existing_issue: Issue
):
    response = client.patch("/issues/101", json={"title": ""})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]

    # Refresh and verify Issue #101 is unchanged
    issue = session.get(Issue, 101)
    session.refresh(issue)
    assert issue.title == "Login fails"
    assert issue.status == "open"


def test_update_issue_null_title(
    client: TestClient, session: Session, existing_issue: Issue
):
    response = client.patch("/issues/101", json={"title": None})
    assert response.status_code == 422
    assert response.json() == {"detail": "Fields cannot be null"}
    issue = session.get(Issue, 101)
    session.refresh(issue)
    assert issue.title == "Login fails"
    assert issue.status == "open"


def test_update_issue_null_status(
    client: TestClient, session: Session, existing_issue: Issue
):
    response = client.patch("/issues/101", json={"status": None})
    assert response.status_code == 422
    assert response.json() == {"detail": "Fields cannot be null"}
    issue = session.get(Issue, 101)
    session.refresh(issue)
    assert issue.title == "Login fails"
    assert issue.status == "open"


def test_update_issue_empty_body(client: TestClient, existing_issue: Issue):
    response = client.patch("/issues/101", json={})
    assert response.status_code == 200
    get_response = client.get("/issues/101")
    assert get_response.status_code == 200

    assert get_response.json() == {
        "id": 101,
        "title": "Login fails",
        "status": "open",
    }


def test_update_issue_both_fields(client: TestClient, existing_issue: Issue):
    # PATCH /issues/101
    # Update title and status
    response = client.patch(
        "/issues/101",
        json={"title": "Login fails after password reset", "status": "closed"},
    )
    assert response.status_code == 200

    # Send GET /issues/101
    # Verify the changes are retrievable
    get_response = client.get("/issues/101")
    assert get_response.status_code == 200

    assert get_response.json() == {
        "id": 101,
        "title": "Login fails after password reset",
        "status": "closed",
    }


def test_update_issue_invalid_id(client: TestClient):
    response = client.patch("issues/abc", json={"status": "closed"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "issue_id"]


def test_update_issue_invalid_body_and_missing_id(client: TestClient):
    response = client.patch("issues/999", json={"status": "pending"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "status"]


def test_delete_issue_success(
    client: TestClient, session: Session, existing_issue: Issue
):
    # DELETE /issues/101
    response = client.delete("/issues/101")
    assert response.status_code == 204
    assert response.content == b""

    db_issue = session.get(Issue, 101)
    assert db_issue is None

    response = client.get("/issues/101 ")
    assert response.status_code == 404
    assert response.json() == {"detail": "Issue not found"}


def test_delete_issue_not_found(client: TestClient):
    # DELETE /issues/999
    response = client.delete("/issues/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Issue not found"}


def test_delete_issue_invalid_id(client: TestClient):
    # DELETE /issues/abc
    response = client.delete("/issues/abc")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "issue_id"]


def test_delete_issue_twice(client: TestClient, existing_issue: Issue):
    # First DELETE /issues/101
    # Assert 204
    response = client.delete("/issues/101")
    assert response.status_code == 204

    # Second DELETE /issues/101
    # Assert 404
    response = client.delete("/issues/101")
    assert response.status_code == 404


def test_delete_only_target_issue(
    client: TestClient, session: Session, existing_issue: Issue
):
    # Issue #101 already exists because of the fixture

    # Create only Issue #102
    issue_2 = Issue(id=102, title="Battery issue", status="open")
    session.add(issue_2)
    session.commit()

    # Delete Issue #101
    response = client.delete("/issues/101")
    assert response.status_code == 204

    # Verify Issue #101 was deleted
    deleted_issue = session.get(Issue, 101)
    assert deleted_issue is None

    # Verify Issue #102 still exists
    remaining_issue = session.get(Issue, 102)
    assert remaining_issue is not None
    session.refresh(remaining_issue)

    assert remaining_issue.title == "Battery issue"
    assert remaining_issue.status == "open"
