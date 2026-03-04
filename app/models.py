"""
Database ORM Models Module

This module defines SQLAlchemy ORM models for the application entities:
- Dataset: Container for organizing handwriting samples
- Student: Individual contributor of handwriting samples
- HandwritingSample: Individual handwriting sample with embedding
"""

from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
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
    name = Column(String, nullable=False)

    students = relationship("Student", back_populates="dataset")


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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))

    dataset = relationship("Dataset", back_populates="students")


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
    embedding = Column(LargeBinary, nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    student = relationship("Student")