from sqlmodel import SQLModel, Field


class Issue(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1)
    status: str = Field(default="open")
