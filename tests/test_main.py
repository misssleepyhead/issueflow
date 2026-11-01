from fastapi.testclient import TestClient
from main import app
from database import get_session
import main
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

    # Create and yield TestClient(app)
    client = TestClient(app)
    yield client

    # Clear dependency overrides after testing
    app.dependency_overrides.clear()


def test_health_check(client: TestClient):
    # 1. Send a GET request to /health
    response = client.get("/health")
    # 2. Assert status code == 200
    assert response.status_code == 200
    # 3. Assert response body == {"status": "ok"}
    assert response.json() == {"status": "ok"}


def test_get_issues(client: TestClient, session: Session):
    # Create an Issue object:
    # id = 101
    # title = "Login fails"
    # status = "open"
    issue_1 = Issue(id=101, title="Login fails", status="open")

    # Add the Issue to the Session
    # and commit the transaction
    session.add(issue_1)
    session.commit()

    # Send GET /issues using client
    response = client.get("/issues")

    # Assert response.status_code == 200
    assert response.status_code == 200

    # Extract the issues list from response.json()
    returned_json = response.json()

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


def test_get_issue_success(client: TestClient, session: Session):
    issue_1 = Issue(id=101, title="Login fails", status="open")
    session.add(issue_1)
    session.commit()

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

    # check that the total issue list should not change
    statement = select(Issue)
    results = session.exec(statement)
    issues_list = results.all()
    assert len(issues_list) == 0


def test_create_issue_empty_title(client: TestClient, session: Session):

    response = client.post("/issues", json={"title": ""})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]

    # check that the total issue list should not change
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

    # check that the total issue list should not change
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

    assert response.json() == {"id": 104, "title": "Battery issue", "status": "open"}
