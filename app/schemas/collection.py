# # app/schemas/collection.py
# from pydantic import BaseModel, Field, HttpUrl
# from typing import List, Optional
# from uuid import UUID
# from datetime import datetime
# from app.schemas.book import BookResponse # To show content details within a collection item

# # --- CollectionItem Schemas ---
# class CollectionItemBase(BaseModel):
#     content_id: UUID
#     sort_order: int = Field(default=0, ge=0)
#     notes: Optional[str] = None

# class CollectionItemCreate(CollectionItemBase):
#     pass

# class CollectionItemUpdate(BaseModel):
#     sort_order: Optional[int] = Field(None, ge=0)
#     notes: Optional[str] = None

# class CollectionItemResponse(CollectionItemBase):
#     id: UUID
#     collection_id: UUID
#     added_at: datetime
#     # Optionally include full content details
#     content_detail: Optional[BookResponse] = None 

#     class Config:
#         from_attributes = True

# # --- Collection Schemas ---
# class CollectionBase(BaseModel):
#     name: str = Field(..., min_length=3, max_length=200)
#     description: Optional[str] = None
#     cover_image_url: Optional[HttpUrl] = None
#     is_public: bool = True
#     is_featured: bool = False

# class CollectionCreate(CollectionBase):
#     # slug: Optional[str] = None # Slug will be auto-generated
#     pass

# class CollectionUpdate(BaseModel):
#     name: Optional[str] = Field(None, min_length=3, max_length=200)
#     description: Optional[str] = None
#     cover_image_url: Optional[HttpUrl] = None
#     is_public: Optional[bool] = None
#     is_featured: Optional[bool] = None

# class CollectionResponse(CollectionBase):
#     id: UUID
#     slug: str
#     # curator_id: Optional[UUID] = None # If you implement curators
#     created_at: datetime
#     updated_at: datetime
#     items: List[CollectionItemResponse] = [] # List of items in the collection

#     class Config:
#         from_attributes = True