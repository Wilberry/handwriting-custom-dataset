"""
Students Router Module

This module provides REST API endpoints for managing student records.
Students are associated with datasets and serve as containers for handwriting samples.

Routes:
    - POST /students/: Create a new student
    - GET /students/{dataset_id}: Retrieve all students in a dataset
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..audit import record_event
from ..security import require_api_key
from ..storage import delete_reference_image

# Initialize router with prefix and tags for API documentation
router = APIRouter(prefix="/students", tags=["Students"], dependencies=[Depends(require_api_key)])


@router.post("/", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: schemas.StudentCreate, request: Request, db: Session = Depends(get_db)):
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
    if not crud.get_dataset(db, student.dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        created = crud.create_student(db, student.name, student.dataset_id)
        record_event(db, request, "student.created", "student", created.id)
        return created
    except crud.DuplicateRecordError as exc:
        raise HTTPException(
            status_code=409, detail="Student name already exists in this dataset"
        ) from exc


@router.get("/{dataset_id}", response_model=list[schemas.StudentResponse])
def list_students(
    dataset_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
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
    if not crud.get_dataset(db, dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")
    return crud.get_students_by_dataset(db, dataset_id, offset, limit)


@router.put("/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    student_id: int,
    payload: schemas.StudentNameUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    try:
        updated = crud.update_student(db, student, payload.name)
        record_event(db, request, "student.updated", "student", updated.id)
        return updated
    except crud.DuplicateRecordError as exc:
        raise HTTPException(
            status_code=409, detail="Student name already exists in this dataset"
        ) from exc


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, request: Request, db: Session = Depends(get_db)) -> None:
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    image_paths = crud.delete_student(db, student)
    for image_path in image_paths:
        delete_reference_image(image_path)
    record_event(
        db,
        request,
        "student.deleted",
        "student",
        student_id,
        {"removed_sample_files": len(image_paths)},
    )
