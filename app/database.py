"""
Database Configuration Module

This module configures SQLAlchemy ORM for database operations.
It sets up the SQLite database engine, session factory, and declarative base.
"""

from collections.abc import Generator
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create database engine with SQLite connection
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Configure session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM model definitions
Base = declarative_base()


def get_db() -> Generator:
    """Yield one database session per request and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
