"""
Handwriting Recognition API - Main Application Module

FastAPI application for handwriting recognition with custom dataset support.
Provides endpoints for dataset management, student management, sample uploads,
and handwriting recognition predictions.

Key Features:
    - Dataset Management: Create and manage custom handwriting datasets
    - Student Management: Register students and organize samples
    - Sample Upload: Upload handwriting samples with automatic embedding extraction
    - Handwriting Recognition: Compare new samples against stored samples using embeddings
    - Configurable Matching: Adjustable similarity threshold for predictions

Routes:
    - / : Health check endpoint
    - /datasets : Dataset management endpoints
    - /students : Student management endpoints
    - /samples : Sample upload endpoints
    - /predict : Handwriting recognition prediction endpoint
    - /samples : List all stored samples
"""

from fastapi import FastAPI, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
import numpy as np
from app.database import engine, SessionLocal
from app import models
from app.routers import datasets, students, samples
from app.ml import extract_embedding, compare_embeddings

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI application instance
app = FastAPI(title="Handwriting Recognition Production API")

# Include routers for modular endpoint organization
app.include_router(datasets.router)
app.include_router(students.router)
app.include_router(samples.router)


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


@app.get("/")
def root():
    """
    Health check endpoint.
    
    Returns:
        dict: Simple response indicating API is running.
    """
    return {"message": "Production API Running"}


@app.post("/predict/")
async def predict(
    dataset_id: int = Form(...),
    threshold: float = Form(0.75),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Predict the student identity from a handwriting sample.
    
    Compares a new handwriting sample against all samples in a dataset
    to identify the most likely student. Uses cosine similarity on embeddings
    with a configurable threshold for confidence filtering.
    
    Args:
        dataset_id (int): ID of the dataset to search within.
        threshold (float): Minimum similarity score (0-1) for a confident match.
                          Default: 0.75. Lower values = more permissive matching.
        file (UploadFile): The handwriting sample image to recognize.
        db (Session): Database session dependency, automatically injected by FastAPI.
    
    Returns:
        dict: Prediction result containing:
            - match (bool): Whether a confident match was found
            - predicted_student_id (int, optional): ID of matched student if match=True
            - similarity_score (float): Score of the best match (0-1)
            - message (str, optional): Additional context message
    
    Process:
        1. Saves uploaded file temporarily
        2. Extracts embedding from handwriting image
        3. Retrieves all samples in the specified dataset
        4. Compares embedding against all stored samples
        5. Returns best match if score exceeds threshold
    """
    # Save uploaded file temporarily
    file_location = f\"uploads/{file.filename}\"
    
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    
    # Extract embedding from the new handwriting sample
    new_embedding = extract_embedding(file_location)
    
    # Retrieve all handwriting samples in the specified dataset
    # Uses a join to filter samples by dataset through the student relationship
    samples_list = (
        db.query(models.HandwritingSample)
        .join(models.Student)
        .filter(models.Student.dataset_id == dataset_id)
        .all()
    )
    
    # Handle case where dataset has no samples
    if not samples_list:
        return {"message": "No handwriting samples in this dataset"}
    
    # Extract embeddings and student IDs from stored samples
    stored_embeddings = []
    student_ids = []
    
    for sample in samples_list:
        emb = np.frombuffer(sample.embedding, dtype=np.float32)
        stored_embeddings.append(emb)
        student_ids.append(sample.student_id)
    
    # Compare new embedding against all stored embeddings
    similarities = compare_embeddings(new_embedding, stored_embeddings)
    
    # Find the best match
    best_match_index = np.argmax(similarities)
    best_score = similarities[best_match_index]
    
    # Apply threshold for confident matching
    if best_score < threshold:
        return {
            "match": False,
            "similarity_score": float(best_score),
            "message": "No confident match found"
        }
    
    return {
        "match": True,
        "predicted_student_id": student_ids[best_match_index],
        "similarity_score": float(best_score)
    }


@app.get("/samples/")
def list_samples(db: Session = Depends(get_db)):
    """
    Retrieve all handwriting samples in the system.
    
    Returns metadata for all uploaded handwriting samples without embedding data.
    Useful for auditing and sample inventory management.
    
    Args:
        db (Session): Database session dependency, automatically injected by FastAPI.
    
    Returns:
        list[dict]: List of sample metadata containing:
            - id (int): Unique sample identifier
            - image_path (str): File path to the stored image
            - student_id (int): ID of the student who provided the sample
    """
    samples = db.query(models.HandwritingSample).all()
    return [
        {
            "id": s.id,
            "image_path": s.image_path,
            "student_id": s.student_id
        }
        for s in samples
    ]