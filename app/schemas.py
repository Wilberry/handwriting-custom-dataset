"""
Pydantic Schemas Module

This module defines Pydantic models for request/response validation.
These schemas ensure data consistency and provide API documentation.
"""

from pydantic import BaseModel


# ==================== DATASET SCHEMAS ====================

class DatasetBase(BaseModel):
    """Base schema for dataset attributes."""
    name: str


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset."""
    pass


class DatasetResponse(DatasetBase):
    """Schema for dataset response data including ID."""
    id: int

    class Config:
        from_attributes = True


# ==================== STUDENT SCHEMAS ====================

class StudentBase(BaseModel):
    """Base schema for student attributes."""
    name: str
    dataset_id: int


class StudentCreate(StudentBase):
    """Schema for creating a new student."""
    pass


class StudentResponse(StudentBase):
    """Schema for student response data including ID."""
    id: int

    class Config:
        from_attributes = True


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
    image_path: str
    student_id: int

    class Config:
        from_attributes = True