# app/schemas/story.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.content import LanguageCode, ContentStatus # Assuming these enums are in content.py or globally accessible

# Base for common story fields
class StoryBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    language: str = LanguageCode.EN.value # Defaulting
    tags: Optional[List[str]] = Field(None, max_items=20)
    cover_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    # No file_url for text stories usually, unless it's an attachment

class StoryCreate(StoryBase):
    category_id: Optional[str] = None
    author_name: Optional[str] = Field(None, max_length=200) 
    status: Optional[str] = ContentStatus.PUBLISHED.value
    featured: Optional[bool] = False
    premium_content: bool = False
    # content_type and sub_type will be set by CRUDStory

class StoryUpdate(StoryBase): # Specific fields for updating a story
    category_id: Optional[str] = None
    author_name: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = ContentStatus.PUBLISHED.value
    featured: Optional[bool] = None
    premium_content: Optional[bool] = None

class StoryResponse(StoryBase): # Inherits fields from StoryBase
    id: UUID
    slug: str
    # These are from Content model but relevant to Story presentation
    content_type: str # Will be ARTICLE
    sub_type: str    # Will be STORY
    author_id: Optional[UUID] = None
    author_name: Optional[str] = None
    category_id: Optional[UUID] = None # Or str
    status: str
    published_at: Optional[datetime] = None
    featured: bool
    premium_content: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True