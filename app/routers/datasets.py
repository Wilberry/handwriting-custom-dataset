"""
Datasets Router Module

This module provides REST API endpoints for managing handwriting recognition datasets.
It handles dataset creation and retrieval operations through a FastAPI router.

Routes:
    - POST /datasets/: Create a new dataset
    - GET /datasets/: Retrieve all datasets
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import schemas, crud

# Initialize router with prefix and tags for API documentation
router = APIRouter(prefix="/datasets", tags=["Datasets"])


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


@router.post("/", response_model=schemas.DatasetResponse)
def create_dataset(dataset: schemas.DatasetCreate, db: Session = Depends(get_db)):
    """
    Create a new handwriting dataset.
    
    Creates a new dataset entry in the database with the provided name.
    This endpoint allows users to register custom datasets for model training.
    
    Args:
        dataset (schemas.DatasetCreate): Dataset creation request containing dataset name.
        db (Session): Database session dependency, automatically injected by FastAPI.
    
    Returns:
        schemas.DatasetResponse: Created dataset object with ID and metadata.
    """
    return crud.create_dataset(db, dataset.name)


@router.get("/", response_model=list[schemas.DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """
    Retrieve all available datasets.
    
    Fetches a list of all registered datasets from the database.
    This endpoint provides visibility into all datasets available in the system.
    
    Args:
        db (Session): Database session dependency, automatically injected by FastAPI.
    
    Returns:
        list[schemas.DatasetResponse]: List of all dataset objects with their metadata.
    """
    return crud.get_datasets(db)
