# app/schemas/category.py (New File - Placeholder)
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: Optional[str] = Field(None, max_length=120, description="Auto-generated if not provided")
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None
    color_code: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$") # Hex color
    parent_id: Optional[str] = None # UUID as string
    sort_order: int = 0
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None
    color_code: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: UUID
    # children: List['CategoryResponse'] = [] # For hierarchical display

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# For hierarchical display, Pydantic needs help with forward references
# if CategoryResponse is used within itself for 'children'.
# This is one way to do it after the class definition:
# CategoryResponse.model_rebuild() 
# Pydantic v2 handles this better with typing.List['CategoryResponse']