from fastapi import FastAPI

app = FastAPI(title="IssueFlow API")


# Implement GET /health
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Implement GET /issues
@app.get("/issues")
def get_issues():
    return {"issues": []}
