"""
Pydantic Schemas Module

This module defines Pydantic models for request/response validation.
These schemas ensure data consistency and provide API documentation.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NamedModel(BaseModel):
    """Shared validation for human-readable names."""

    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value


# ==================== DATASET SCHEMAS ====================


class DatasetBase(NamedModel):
    """Base schema for dataset attributes."""


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset."""

    pass


class DatasetResponse(DatasetBase):
    """Schema for dataset response data including ID."""

    id: int

    model_config = ConfigDict(from_attributes=True)


# ==================== STUDENT SCHEMAS ====================


class StudentBase(NamedModel):
    """Base schema for student attributes."""

    dataset_id: int = Field(gt=0)


class StudentCreate(StudentBase):
    """Schema for creating a new student."""

    pass


class StudentNameUpdate(NamedModel):
    """Schema for renaming an existing student."""


class StudentResponse(StudentBase):
    """Schema for student response data including ID."""

    id: int

    model_config = ConfigDict(from_attributes=True)


# ==================== HANDWRITING SAMPLE SCHEMAS ====================


class HandwritingSampleResponse(BaseModel):
    """
    Schema for handwriting sample response data.

    Attributes:
        id (int): Unique sample identifier.
        image_path (str): Path to the stored image file.
        student_id (int): ID of the student who provided the sample.
    """

    id: int
    student_id: int
    embedding_model: str
    embedding_dimension: int

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    id: int
    event_type: str
    actor: str
    entity_type: str
    entity_id: int | None
    request_id: str | None
    details: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionCandidate(BaseModel):
    student_id: int
    student_name: str
    similarity_score: float


class PredictionResponse(BaseModel):
    match: bool
    predicted_student_id: int | None
    predicted_student_name: str | None
    similarity_score: float | None
    top_matches: list[PredictionCandidate]
    message: str | None
