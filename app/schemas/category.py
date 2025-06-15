# app/schemas/category.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.category import CategoryScopeType # Import the new enum

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color_code: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    type: str = CategoryScopeType.BOOK.value
    parent_id: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color_code: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    type: Optional[str] = None 
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class CategoryResponse(CategoryBase): # Inherit from CategoryBase to get most fields
    id: UUID
    type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Resolve forward reference for children (Pydantic v2 handles this better, but good practice)
# CategoryResponse.model_rebuild() # For Pydantic v1