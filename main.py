from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="IssueFlow API")

issues = [
    {"id": 101, "title": "Login fails", "status": "open"},
    {"id": 102, "title": "App crashes", "status": "closed"},
    {"id": 103, "title": "Slow loading", "status": "open"},
]


class IssueCreate(BaseModel):
    title: str = Field(min_length=1)
    status: Literal["open", "closed"] = Field(default="open")


# Implement GET /health
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Implement GET /issues
@app.get("/issues")
def get_issues():
    return {"issues": issues}


@app.get("/issues/{issue_id}")
def get_issue(issue_id: int):
    # Search the issues list for the requested ID.
    for issue in issues:
        if issue["id"] == issue_id:
            # If found, return that issue dictionary.
            return issue
    # If not found, raise HTTPException with status 404.
    raise HTTPException(status_code=404, detail="issue not found")


@app.post("/issues", status_code=201)
def create_issue(issue: IssueCreate):
    #  1: Generate a unique Issue ID
    next_id = max((record["id"] for record in issues), default=100) + 1

    # 2: Convert the Pydantic model
    # into a Python dictionary
    new_issue = issue.model_dump()

    # 3: Add the generated ID
    new_issue["id"] = next_id

    # 4: Save the new Issue in the list
    issues.append(new_issue)

    # 5: Return the created Issue
    return new_issue
