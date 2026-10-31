from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from fastapi import Depends
from sqlmodel import Session, select
from database import get_session
from models import Issue

app = FastAPI(title="IssueFlow API")


class IssueCreate(BaseModel):
    title: str = Field(min_length=1)
    status: Literal["open", "closed"] = Field(default="open")


# Implement GET /health
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Implement GET /issues
@app.get("/issues")
def get_issues(session: Session = Depends(get_session)):
    # Create a SELECT statement for all Issues
    statement = select(Issue)
    # Execute the statement
    results = session.exec(statement)
    issues_list = results.all()
    return {"issues": issues_list}


@app.get("/issues/{issue_id}")
def get_issue(issue_id: int, session: Session = Depends(get_session)):
    # 1: Retrieve the Issue using session.get()
    issue = session.get(Issue, issue_id)

    # 2: If the Issue doesn't exist,
    # raise HTTPException(404)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found.")

    # 3: Return the Issue
    return issue


@app.post("/issues", status_code=201)
def create_issue(issue: IssueCreate, session: Session = Depends(get_session)):

    # 1: Convert the Pydantic model
    # into a Python dictionary
    new_issue = Issue(title=issue.title, status=issue.status)

    # 2: Add the object to the Session
    session.add(new_issue)
    session.commit()
    session.refresh(new_issue)

    return new_issue
