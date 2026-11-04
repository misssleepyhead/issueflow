from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal
from sqlmodel import Session, select
from database import get_session
from models import Issue
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="IssueFlow API")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def homepage():
    return FileResponse(STATIC_DIR / "index.html")


class IssueCreate(BaseModel):
    title: str = Field(min_length=1)
    status: Literal["open", "closed"] = Field(default="open")


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    status: Literal["open", "closed"] | None = None


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


@app.patch("/issues/{issue_id}")
def update_issue(
    issue_id: int, update: IssueUpdate, session: Session = Depends(get_session)
):
    # Find the existing Issue
    db_issue = session.get(Issue, issue_id)
    if db_issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Extract only the fields provided by the client
    update_part = update.model_dump(exclude_unset=True)
    # Reject explicit None values
    if any(value is None for value in update_part.values()):
        raise HTTPException(status_code=422, detail="Fields cannot be null")

    db_issue.sqlmodel_update(update_part)

    session.add(db_issue)
    session.commit()
    session.refresh(db_issue)
    return db_issue


@app.delete("/issues/{issue_id}", status_code=204)
def delete_issue(issue_id: int, session: Session = Depends(get_session)):
    db_issue = session.get(Issue, issue_id)
    if db_issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    session.delete(db_issue)
    session.commit()
