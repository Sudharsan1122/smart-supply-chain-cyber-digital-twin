"""SQLAlchemy 2.0 database engine and session management."""
from __future__ import annotations

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _build_engine_args(url: str) -> dict[str, object]:
    """Build SQLAlchemy engine kwargs based on database dialect."""
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}


engine = create_engine(settings.database_url, **_build_engine_args(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class for all SCDT ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session via dependency injection.

    Yields:
        Session: Active SQLAlchemy ORM session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
