# app/schemas/bookmark.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
#from app.schemas.content import ContentMinimalResponse # A slimmed-down content response for bookmarks


class ContentMinimalResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    content_type: str # Or use the enum value
    sub_type: Optional[str] = None
    cover_image_url: Optional[str] = None
    # ... any other minimal fields you want to show in a bookmark list

    class Config:
        from_attributes = True

class BookmarkBase(BaseModel):
    content_id: UUID
    notes: Optional[str] = None

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkUpdate(BaseModel):
    notes: Optional[str] = None # Only notes can be updated

class BookmarkResponse(BookmarkBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    content: Optional[ContentMinimalResponse] = None # To show bookmarked content details

    class Config:
        from_attributes = True
