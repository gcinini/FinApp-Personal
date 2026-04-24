"""Pytest configuration: in-memory SQLite for fast tests."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from finapp.db.base import Base
import finapp.models  # noqa: F401


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
