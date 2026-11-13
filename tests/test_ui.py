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

    page.get_by_placeholder("Enter issue title").fill(issue_title)
    page.get_by_role("button", name="Add Issue").click()

    # Locate the table row containing title
    row = page.locator("#issues-body tr").filter(has_text=issue_title)
    # Assert the row is visible
    expect(row).to_have_count(1)
    expect(row).to_be_visible()

    status_cell = row.locator("td").nth(2)
    expect(status_cell).to_have_text("open")

    # Close
    row.get_by_role("button", name="Close").click()
    expect(status_cell).to_have_text("closed")

    # Reopen
    row.get_by_role("button", name="Reopen").click()
    expect(status_cell).to_have_text("open")

    # Delete
    row.get_by_role("button", name="Delete").click()
    expect(row).to_have_count(0)


def test_empty_title_validation(page: Page):
    page.goto(BASE_URL)

    # Locate the title input
    # Fill it with an empty string ""
    title_input = page.get_by_placeholder("Enter issue title")
    title_input.fill("")
    page.get_by_role("button", name="Add Issue").click()

    # Verify that the input is invalid because
    # the required field is empty.
    is_required = title_input.evaluate("(element) => element.required")
    assert is_required is True

    # Verify that "Issue created successfully"
    # is NOT displayed
    expect(page.locator("#message")).not_to_have_text("Issue created successfully")


def test_create_issue_after_reload(page: Page, issue_title: str):
    page.goto(BASE_URL)

    # Create an Issue using issue_title
    page.get_by_placeholder("Enter issue title").fill(issue_title)
    page.get_by_role("button", name="Add Issue").click()

    # Locate the matching table row
    row = page.locator("#issues-body tr").filter(has_text=issue_title)
    expect(row).to_have_count(1)
    page.reload()

    # Verify the Issue still exists
    # and its status is "open"
    expect(row).to_be_visible()
    status_cell = row.locator("td").nth(2)
    expect(status_cell).to_have_text("open")


def test_status_persistence_after_reload(page: Page, issue_title: str):
    page.goto(BASE_URL)

    page.get_by_placeholder("Enter issue title").fill(issue_title)
    page.get_by_role("button", name="Add Issue").click()
    row = page.locator("#issues-body tr").filter(has_text=issue_title)
    status_cell = row.locator("td").nth(2)
    expect(status_cell).to_have_text("open")

    row.get_by_role("button", name="Close").click()
    expect(status_cell).to_have_text("closed")
    page.reload()

    expect(status_cell).to_have_text("closed")

    row.get_by_role("button", name="Reopen").click()

    expect(status_cell).to_have_text("open")
    page.reload()
    expect(status_cell).to_have_text("open")


def test_get_issues_api_failure(page: Page):
    # Intercept GET /issues using page.route()
    # Simulate HTTP 500
    page.route(
        "**/issues",
        lambda route: route.fulfill(
            status=500,
            content_type="application/json",
            body='{"detail":"Internal server error"}',
        ),
    )

    page.goto(BASE_URL)
    expect(page.locator("#message")).to_have_text("Failed to load issues")
