from sqlmodel import Field, Session, SQLModel, create_engine, select

from datetime import datetime


class Log(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=False)
    severity: str | None = Field(default=None, index=True)
    textPayload: str | None = Field(default=None, index=False)
    resource: str | None = Field(default=None, index=True)
