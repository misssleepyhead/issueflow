from fastapi import FastAPI, HTTPException

app = FastAPI(title="IssueFlow API")

issues = [
    {"id": 101, "title": "Login fails", "status": "open"},
    {"id": 102, "title": "App crashes", "status": "closed"},
    {"id": 103, "title": "Slow loading", "status": "open"},
]


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
