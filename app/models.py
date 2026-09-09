"""
Database ORM Models Module

This module defines SQLAlchemy ORM models for the application entities:
- Dataset: Container for organizing handwriting samples
- Student: Individual contributor of handwriting samples
- HandwritingSample: Individual handwriting sample with embedding
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from .database import Base


class Dataset(Base):
    """
    Dataset model representing a collection of handwriting samples.

    Attributes:
        id (int): Primary key, unique dataset identifier.
        name (str): Name of the dataset.
        students (relationship): List of students associated with this dataset.
    """

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)

    students = relationship("Student", back_populates="dataset", cascade="all, delete-orphan")


class Student(Base):
    """
    Student model representing an individual contributor of handwriting samples.

    Attributes:
        id (int): Primary key, unique student identifier.
        name (str): Name of the student.
        dataset_id (int): Foreign key referencing the associated dataset.
        dataset (relationship): Reference to the parent Dataset object.
    """

    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("dataset_id", "name", name="uq_student_dataset_name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    dataset = relationship("Dataset", back_populates="students")
    samples = relationship(
        "HandwritingSample", back_populates="student", cascade="all, delete-orphan"
    )


class HandwritingSample(Base):
    """
    HandwritingSample model representing a single handwriting image and its embedding.

    Attributes:
        id (int): Primary key, unique sample identifier.
        image_path (str): File path to the stored handwriting image.
        embedding (bytes): Serialized numpy array containing the ML model embedding.
        student_id (int): Foreign key referencing the contributing student.
        student (relationship): Reference to the parent Student object.
    """

    __tablename__ = "handwriting_samples"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=False)
    embedding_model = Column(String(120), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    student = relationship("Student", back_populates="samples")


class AuditEvent(Base):
    """Durable security and data-lifecycle event without secret payloads."""

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    actor = Column(String(120), nullable=False)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(Integer, nullable=True)
    request_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=False, default="{}")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
