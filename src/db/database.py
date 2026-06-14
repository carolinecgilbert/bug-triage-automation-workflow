"""SQLAlchemy database setup."""

from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


load_dotenv()

DEFAULT_DATABASE_URL = "postgresql+psycopg://bugtriage:bugtriage@localhost:5432/bugtriage"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables for the MVP.

    Production systems should use Alembic migrations instead of
    `Base.metadata.create_all()`. For this project step, create_all keeps local
    Docker Postgres and test SQLite setup simple.
    """
    from src.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

