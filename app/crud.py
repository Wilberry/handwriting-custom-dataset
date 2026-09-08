"""
CRUD Operations Module

This module provides create and read operations for the application data models.
It serves as the data access layer for the application, handling all database interactions.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models
from .ml import EMBEDDING_DIMENSION, EMBEDDING_MODEL


class DuplicateRecordError(ValueError):
    """Raised when a unique database record already exists."""


class InvalidRecordError(ValueError):
    """Raised when a record contains invalid domain data."""


def _normalize_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise InvalidRecordError("Name must not be blank")
    if len(normalized) > 120:
        raise InvalidRecordError("Name must not exceed 120 characters")
    return normalized


def _commit(db: Session, record):
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateRecordError("Record already exists") from exc


def get_dataset(db: Session, dataset_id: int):
    return db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()


def get_student(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_sample(db: Session, sample_id: int):
    return (
        db.query(models.HandwritingSample).filter(models.HandwritingSample.id == sample_id).first()
    )


# ==================== DATASET OPERATIONS ====================


def create_dataset(db: Session, name: str):
    """
    Create a new dataset.

    Args:
        db (Session): Database session.
        name (str): Name of the dataset.

    Returns:
        models.Dataset: The created dataset object.
    """
    db_dataset = models.Dataset(name=_normalize_name(name))
    return _commit(db, db_dataset)


def get_datasets(db: Session, offset: int = 0, limit: int = 100):
    """
    Retrieve all datasets from the database.

    Args:
        db (Session): Database session.

    Returns:
        list[models.Dataset]: List of all datasets.
    """
    return db.query(models.Dataset).order_by(models.Dataset.id).offset(offset).limit(limit).all()


def update_dataset(db: Session, dataset: models.Dataset, name: str):
    dataset.name = _normalize_name(name)
    return _commit(db, dataset)


def delete_dataset(db: Session, dataset: models.Dataset) -> list[str]:
    image_paths = [sample.image_path for student in dataset.students for sample in student.samples]
    db.delete(dataset)
    db.commit()
    return image_paths


# ==================== STUDENT OPERATIONS ====================


def create_student(db: Session, name: str, dataset_id: int):
    """
    Create a new student record and associate with a dataset.

    Args:
        db (Session): Database session.
        name (str): Name of the student.
        dataset_id (int): ID of the dataset to associate with.

    Returns:
        models.Student: The created student object.
    """
    db_student = models.Student(name=name, dataset_id=dataset_id)
    db_student.name = _normalize_name(name)
    return _commit(db, db_student)


def get_students_by_dataset(db: Session, dataset_id: int, offset: int = 0, limit: int = 100):
    """
    Retrieve all students belonging to a specific dataset.

    Args:
        db (Session): Database session.
        dataset_id (int): ID of the dataset.

    Returns:
        list[models.Student]: List of students in the dataset.
    """
    return (
        db.query(models.Student)
        .filter(models.Student.dataset_id == dataset_id)
        .order_by(models.Student.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_student(db: Session, student: models.Student, name: str):
    student.name = _normalize_name(name)
    return _commit(db, student)


def delete_student(db: Session, student: models.Student) -> list[str]:
    image_paths = [sample.image_path for sample in student.samples]
    db.delete(student)
    db.commit()
    return image_paths


# ==================== HANDWRITING SAMPLE OPERATIONS ====================


def create_handwriting_sample(
    db: Session,
    image_path: str,
    student_id: int,
    embedding: bytes,
    embedding_model: str = EMBEDDING_MODEL,
    embedding_dimension: int = EMBEDDING_DIMENSION,
):
    """
    Create a new handwriting sample record with embedding.

    Args:
        db (Session): Database session.
        image_path (str): File path to the uploaded handwriting image.
        student_id (int): ID of the student who provided the sample.
        embedding (bytes, optional): Serialized embedding vector from ML model.

    Returns:
        models.HandwritingSample: The created sample object.
    """
    db_sample = models.HandwritingSample(
        image_path=image_path,
        student_id=student_id,
        embedding=embedding,
        embedding_model=embedding_model,
        embedding_dimension=embedding_dimension,
    )
    return _commit(db, db_sample)


def delete_handwriting_sample(db: Session, sample: models.HandwritingSample) -> str:
    image_path = sample.image_path
    db.delete(sample)
    db.commit()
    return image_path
