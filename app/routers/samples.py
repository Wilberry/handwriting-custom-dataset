"""
Handwriting Samples Router Module

This module provides REST API endpoints for managing handwriting samples.
It handles file uploads, embedding extraction, and sample metadata storage.

Routes:
    - POST /samples/{student_id}: Upload a handwriting sample for a student
"""

import os
import shutil
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import crud, schemas
from app.ml import extract_embedding

# Initialize router with prefix and tags for API documentation
router = APIRouter(prefix="/samples", tags=["Samples"])

# Directory for storing uploaded handwriting sample files
UPLOAD_DIR = "uploads"


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


@router.post("/{student_id}", response_model=schemas.HandwritingSampleResponse)
def upload_sample(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
    # Save uploaded file to local storage
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract embedding representation from the handwriting sample
    embedding = extract_embedding(file_path)
    embedding_bytes = embedding.tobytes()

    # Store sample and embedding metadata in database
    return crud.create_handwriting_sample(db, file_path, student_id, embedding_bytes)
