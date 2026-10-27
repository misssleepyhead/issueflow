from sqlmodel import SQLModel, create_engine
from models import Issue

sqlite_file_name = "issueflow.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
