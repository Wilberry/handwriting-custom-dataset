"""
Database Configuration Module

This module configures SQLAlchemy ORM for database operations.
It sets up the SQLite database engine, session factory, and declarative base.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
DATABASE_URL = "sqlite:///./app.db"

# Create database engine with SQLite connection
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Configure session factory for database operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base for ORM model definitions
Base = declarative_base()