from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"


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
    expect(page.get_by_role("columnheader", name="Title")).to_have_text("Status")
