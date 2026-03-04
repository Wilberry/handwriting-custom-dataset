"""
CRUD Operations Module

This module provides Create, Read, Update, Delete operations for all data models.
It serves as the data access layer for the application, handling all database interactions.
"""

from sqlalchemy.orm import Session
from . import models


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
    db_dataset = models.Dataset(name=name)
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset


def get_datasets(db: Session):
    """
    Retrieve all datasets from the database.
    
    Args:
        db (Session): Database session.
    
    Returns:
        list[models.Dataset]: List of all datasets.
    """
    return db.query(models.Dataset).all()


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
    db_student = models.Student(
        name=name,
        dataset_id=dataset_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_students_by_dataset(db: Session, dataset_id: int):
    """
    Retrieve all students belonging to a specific dataset.
    
    Args:
        db (Session): Database session.
        dataset_id (int): ID of the dataset.
    
    Returns:
        list[models.Student]: List of students in the dataset.
    """
    return db.query(models.Student).filter(
        models.Student.dataset_id == dataset_id
    ).all()


# ==================== HANDWRITING SAMPLE OPERATIONS ====================

def create_handwriting_sample(db: Session, image_path: str, student_id: int, embedding=None):
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
        embedding=embedding
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample
