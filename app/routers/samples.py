"""
Handwriting Samples Router Module

This module provides REST API endpoints for managing handwriting samples.
It handles file uploads, embedding extraction, and sample metadata storage.

Routes:
    - POST /samples/{student_id}: Upload a handwriting sample for a student
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas
from app.audit import record_event
from app.ml import extract_embedding
from app.security import require_api_key
from app.storage import delete_reference_image, persist_reference_image
from app.uploads import InvalidUploadError, save_image_upload

# Initialize router with prefix and tags for API documentation
router = APIRouter(prefix="/samples", tags=["Samples"], dependencies=[Depends(require_api_key)])


@router.post(
    "/{student_id}",
    response_model=schemas.HandwritingSampleResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_sample(
    student_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a handwriting sample for a specific student.

    This endpoint handles file uploads, stores them locally, extracts embeddings
    using the ML model, and persists sample metadata to the database.
    The embedding serves as a numerical representation of the handwriting for model training.

    Args:
        student_id (int): The ID of the student submitting the handwriting sample.
        file (UploadFile): The uploaded handwriting image file.
        db (Session): Database session dependency, automatically injected by FastAPI.

    Returns:
        schemas.HandwritingSampleResponse: Metadata of the created sample including
                                          file path, student ID, and embedding reference.

    Process:
        1. Saves the uploaded file to the uploads directory
        2. Extracts numerical embedding from the handwriting image
        3. Stores sample metadata and embedding in the database
    """
    if not crud.get_student(db, student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        file_path = save_image_upload(file)
    except InvalidUploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        embedding = extract_embedding(str(file_path))
        embedding_bytes = embedding.tobytes()
        locator = persist_reference_image(file_path)
        created = crud.create_handwriting_sample(db, locator, student_id, embedding_bytes)
        record_event(db, request, "sample.created", "sample", created.id)
        return created
    except Exception:
        file_path.unlink(missing_ok=True)
        if "locator" in locals():
            delete_reference_image(locator)
        raise


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sample(sample_id: int, request: Request, db: Session = Depends(get_db)) -> None:
    sample = crud.get_sample(db, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    image_path = crud.delete_handwriting_sample(db, sample)
    delete_reference_image(image_path)
    record_event(db, request, "sample.deleted", "sample", sample_id)
