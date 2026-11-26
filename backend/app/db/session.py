from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields one session per request and always closes it.

    Services own their transaction boundaries (`with session.begin():`) so that
    commits happen before the response is sent, never after.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


type DbSession = Annotated[Session, Depends(get_db)]
