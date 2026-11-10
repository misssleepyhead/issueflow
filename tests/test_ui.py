from playwright.sync_api import Page, expect
from uuid import uuid4

import pytest
import httpx
from uuid import uuid4

BASE_URL = "http://127.0.0.1:8001"


@pytest.fixture
def issue_title():
    title = f"E2E issue {uuid4().hex[:8]}"

    # Give the unique title to the test
    yield title

    # Teardown: run even if the test assertion fails
    with httpx.Client(base_url=BASE_URL) as api:
        response = api.get("/issues")
        response.raise_for_status()

        for issue in response.json()["issues"]:
            if issue["title"] == title:
                delete_response = api.delete(f"/issues/{issue['id']}")
                delete_response.raise_for_status()


def test_homepage_title(page: Page):
    page.goto(BASE_URL)

    expect(page.get_by_role("heading", name="IssueFlow")).to_be_visible()


def test_create_form_visible(page: Page):
    page.goto(BASE_URL)

    expect(page.get_by_placeholder("Enter issue title")).to_be_visible()

    expect(page.get_by_role("button", name="Add Issue")).to_be_visible()


def test_issues_table_visible(page: Page):
    page.goto(BASE_URL)
    expect(page.get_by_role("table")).to_be_visible()
    expect(page.get_by_role("columnheader", name="Title")).to_have_text("Title")
    expect(page.get_by_role("columnheader", name="Status")).to_have_text("Status")


def test_issue_crud_workflow(page: Page, issue_title: str):
    page.goto(BASE_URL)

    # Generate a unique title to avoid matching older records
    title = f"E2E issue {uuid4().hex[:8]}"
    page.get_by_placeholder("Enter issue title").fill("Login timeout")
    page.get_by_role("button", name="Add Issue").click()

    # Locate the table row containing title
    row = page.locator("#issues-body tr").filter(has_text="Login timeout")
    # Assert the row is visible
    expect(row).to_have_count(1)
    expect(row).to_be_visible()
    # Assert its status is "open"
    expect(row.get_by_role("cell", name="open")).to_be_visible()

    # Click the "Close" button inside that row
    row.get_by_role("button", name="Close").click()
    # Assert the status becomes "closed"
    expect(row.get_by_role("cell", name="Closed")).to_be_visible()

    # Click the "Reopen" button inside that row
    row.get_by_role("button", name="Reopen").click()
    # Assert the status becomes "open"
    expect(row.get_by_role("columnheader", name="Status")).to_have_text("Open")

    # Click the "Delete" button inside that row
    row.get_by_role("button", name="Delete").click()
    # Assert the matching row no longer exists
    expect(
        page.locator("#issues-body tr").filter(has_text="Login timeout")
    ).to_have_count(0)
