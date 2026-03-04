"""
Students Router Module

This module provides REST API endpoints for managing student records.
Students are associated with datasets and serve as containers for handwriting samples.

Routes:
    - POST /students/: Create a new student
    - GET /students/{dataset_id}: Retrieve all students in a dataset
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import schemas, crud

# Initialize router with prefix and tags for API documentation
router = APIRouter(prefix="/students", tags=["Students"])


def get_db():
    """
    Database session dependency provider.
    
    Provides a SQLAlchemy database session for each request.
    Ensures proper cleanup by closing the session after the request completes.
    
    Yields:
        Session: SQLAlchemy database session for database operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.StudentResponse)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """
    Create a new student record.
    
    Creates a new student entry associated with a specific dataset.
    Students serve as containers for organizing handwriting samples by individual.
    
    Args:
        student (schemas.StudentCreate): Student creation request containing 
                                        name and dataset_id.
        db (Session): Database session dependency, automatically injected by FastAPI.
    
    Returns:
        schemas.StudentResponse: Created student object with ID, name, and dataset association.
    """
    return crud.create_student(
        db,
        student.name,
        student.dataset_id
    )


@router.get("/{dataset_id}", response_model=list[schemas.StudentResponse])
def list_students(dataset_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all students in a specific dataset.
    
    Fetches all student records associated with a given dataset.
    This enables querying students for data organization and sample management.
    
    Args:
        dataset_id (int): The ID of the dataset to retrieve students from.
        db (Session): Database session dependency, automatically injected by FastAPI.
    
    Returns:
        list[schemas.StudentResponse]: List of all students in the specified dataset.
    """
    return crud.get_students_by_dataset(db, dataset_id)
