"""
Datasets Router Module

This module provides REST API endpoints for managing handwriting recognition datasets.
It handles dataset creation and retrieval operations through a FastAPI router.

Routes:
    - POST /datasets/: Create a new dataset
    - GET /datasets/: Retrieve all datasets
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..audit import record_event
from ..security import require_api_key
from ..storage import delete_reference_image

# Initialize router with prefix and tags for API documentation
router = APIRouter(prefix="/datasets", tags=["Datasets"], dependencies=[Depends(require_api_key)])


@router.post("/", response_model=schemas.DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(dataset: schemas.DatasetCreate, request: Request, db: Session = Depends(get_db)):
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
    try:
        created = crud.create_dataset(db, dataset.name)
        record_event(db, request, "dataset.created", "dataset", created.id)
        return created
    except crud.DuplicateRecordError as exc:
        raise HTTPException(status_code=409, detail="Dataset name already exists") from exc


@router.get("/", response_model=list[schemas.DatasetResponse])
def list_datasets(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Retrieve all available datasets.

    Fetches a list of all registered datasets from the database.
    This endpoint provides visibility into all datasets available in the system.

    Args:
        db (Session): Database session dependency, automatically injected by FastAPI.

    Returns:
        list[schemas.DatasetResponse]: List of all dataset objects with their metadata.
    """
    return crud.get_datasets(db, offset, limit)


@router.put("/{dataset_id}", response_model=schemas.DatasetResponse)
def update_dataset(
    dataset_id: int,
    payload: schemas.DatasetCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    dataset = crud.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        updated = crud.update_dataset(db, dataset, payload.name)
        record_event(db, request, "dataset.updated", "dataset", updated.id)
        return updated
    except crud.DuplicateRecordError as exc:
        raise HTTPException(status_code=409, detail="Dataset name already exists") from exc


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, request: Request, db: Session = Depends(get_db)) -> None:
    dataset = crud.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    image_paths = crud.delete_dataset(db, dataset)
    for image_path in image_paths:
        delete_reference_image(image_path)
    record_event(
        db,
        request,
        "dataset.deleted",
        "dataset",
        dataset_id,
        {"removed_sample_files": len(image_paths)},
    )
