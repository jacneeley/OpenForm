""""""
import os
import sqlite3
import secrets
from datetime import datetime as dt
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine

__sqlite_config = {
    "url": "sqlite:///instance/database.db",
    "args": {'check_same_thread': False}
}


def configure_wal():
    """
        Configure Write-Ahead Logging for sqlite3 db.
        for a general overview refer to: https://sqldocs.org/sqlite-write-ahead-logging/
    """
    conn_str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
        __file__))), __sqlite_config['url'].split("sqlite:///", maxsplit=1)[-1])
    # print("opening:", conn_str, ".\nsetting up WAL.")
    conn = sqlite3.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def startup_engine():
    """
    Start the SqlModel engine.
    This will create the db file and the tables if they don't exist.
    Loads the engine context for the app to consume.

    Refer to: 'get_session()' for more.

    Returns:
        SqlModel Engine
    """
    sqlite_url = __sqlite_config['url']
    connect_args = __sqlite_config['args']
    engine = create_engine(sqlite_url, connect_args=connect_args)
    SQLModel.metadata.create_all(engine)

    configure_wal()

    return engine


def get_session():
    """Yield the session with current SqlModel Engine

    Yields:
        The session
    """
    engine = startup_engine()
    with Session(engine) as session:
        yield session


def db_session():
    """
    Summary:
       Creates the session Annotation and designates 'get_session()' as the depedency.
    """
    return Annotated[Session, Depends(get_session)]


class Choices(SQLModel, table=True):
    """A Choice submitted by a respondee via the Appication Form.

    Args:
        SQLModel (_type_): base class for creating pydantic models.
        table (bool, optional): Defaults to True. Creates table on 'startup_engine()'.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    choice: str = Field(index=True)
    count: int = Field(index=True)

    def __init__(self, choice: str, count: int):
        self.id = secrets.token_urlsafe(16)
        self.choice = choice
        self.count = count


class Submission(SQLModel, table=True):
    """
    Pydantic model to capture user data from a form.
    The main purpose of this model is to log encrypted user data so that they can't make multiple submissions.


    Args:
        SQLModel (_type_): base class for creating pydantic models.
        table (bool, optional): Defaults to True. Creates table on 'startup_engine()'.
    """
    user_addr: str = Field(default=None, primary_key=True)
    user_choice: str = Field(index=True)
    create_time: dt = Field(index=True)
