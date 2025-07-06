# app/schemas/collection.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class ContentResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    sub_type: Optional[str] = None # Assuming this is a string representation of an enum
    content_type: str # Assuming this is a string representation of an enum
    status: str # Assuming this is a string representation of an enum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic v2 equivalent of orm_mode
        arbitrary_types_allowed = True # If you have custom types in ContentResponse
        json_encoders = {
            UUID: str, # Ensure UUIDs are serialized as strings
        }

# --- CollectionItem Schemas ---
class CollectionItemBase(BaseModel):
    # content_id is specified in the path for adding, or in payload for bulk add
    sort_order: int = Field(default=0, ge=0)
    notes: Optional[str] = None

class CollectionItemCreate(CollectionItemBase):
    content_id: UUID # Required when creating an item

class CollectionItemUpdate(BaseModel): # Only sort_order and notes are typically updatable for an existing item
    sort_order: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

class CollectionItemResponse(CollectionItemBase):
    id: UUID
    collection_id: UUID
    content_id: UUID # Keep content_id for reference
    added_at: datetime
    content: Optional[ContentResponse] = None # Populate with full Content details

    class Config:
        from_attributes = True

# --- Collection Schemas ---
class CollectionBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    cover_image_url: Optional[str] = None # Assuming HttpUrl conversion is handled elsewhere or stored as string
    is_public: bool = True
    is_featured: bool = False
    tags: Optional[List[str]] = Field(None, max_items=10)

class CollectionCreate(CollectionBase):
    # slug will be auto-generated
    # curator_id might be set automatically from current_user
    pass

class CollectionUpdate(BaseModel): # Fields that can be updated for a collection
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = Field(None, max_items=10)

class CollectionResponse(CollectionBase):
    id: UUID
    slug: str
    curator_id: Optional[UUID] = None # If you implement curators
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CollectionResponseWithItems(CollectionResponse):
    items: List[CollectionItemResponse] = []# Ensure items are always included in this response
