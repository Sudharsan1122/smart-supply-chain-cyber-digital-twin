"""Pytest fixtures providing isolated test database sessions, seeded network, and RBAC JWT headers."""
from __future__ import annotations

from collections.abc import Generator
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.security import RoleEnum, create_access_token
from app.services.db_service import db_service

TEST_DB_URL = "sqlite://"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Create a fresh schema and seeded 10-node network for each test function."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    db_service.seed_initial_data(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient wired to the test SQLAlchemy session."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def planner_headers() -> dict[str, str]:
    """Return Authorization header for an authenticated PLANNER user."""
    tok = create_access_token("planner_user", RoleEnum.PLANNER.value, None)
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    """Return Authorization header for an authenticated ADMIN user."""
    tok = create_access_token("admin_user", RoleEnum.ADMIN.value, None)
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture()
def viewer_headers() -> dict[str, str]:
    """Return Authorization header for an authenticated VIEWER user."""
    tok = create_access_token("viewer_user", RoleEnum.VIEWER.value, None)
    return {"Authorization": f"Bearer {tok}"}
