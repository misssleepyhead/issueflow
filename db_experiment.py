from sqlmodel import Session, select
from database import engine
from models import Issue

new_issue = Issue(title="Battery issue", status="open")


print("Before insert:", new_issue.id)

with Session(engine) as session:
    session.add(new_issue)
    session.commit()
    session.refresh(new_issue)

    print("After insert:", new_issue.id)

print("After the session closes")
print("Issue:", new_issue)


def read_issues():
    with Session(engine) as session:
        statement = select(Issue)
        results = session.exec(statement)
        for issue in results:
            print(issue.id)
            print(issue.title)
            print(issue.status)


def read_issue_by_id(issue_id: int):
    with Session(engine) as session:
        issue = session.get(Issue, issue_id)
        if issue is not None:
            print(
                "Issue found",
                issue.id,
                issue.title,
                issue.status,
            )
        else:
            print("Issue not found")


if __name__ == "__main__":
    read_issues()
    read_issue_by_id(3)
