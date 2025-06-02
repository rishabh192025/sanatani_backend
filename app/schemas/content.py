# app/schemas/content.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.content import ContentType, ContentStatus, LanguageCode, ContentSubType # Import enums
from app.schemas.content_chapter import ContentChapterResponse # Import chapter schema

class ContentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    content_type: ContentType
    sub_type: Optional[ContentSubType] = ContentSubType.GENERAL
    language: LanguageCode = LanguageCode.EN
    tags: Optional[List[str]] = Field(None, max_items=20)
    cover_image_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None
    # file_url for main downloadable if applicable (e.g., full e-book, zip of audio)
    file_url: Optional[HttpUrl] = None 

class ContentCreate(ContentBase):
    category_id: Optional[str] = None # Assuming category ID is passed as string UUID
    premium_content: bool = False
    author_name: Optional[str] = Field(None, max_length=200) 
    status: ContentStatus = ContentStatus.DRAFT

class ContentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    content_type: Optional[ContentType] = None
    sub_type: Optional[ContentSubType] = None
    category_id: Optional[str] = None
    language: Optional[LanguageCode] = None
    tags: Optional[List[str]] = Field(None, max_items=20)
    status: Optional[ContentStatus] = None
    featured: Optional[bool] = None
    premium_content: Optional[bool] = None
    cover_image_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None
    file_url: Optional[HttpUrl] = None
    author_name: Optional[str] = Field(None, max_length=200)

class ContentResponse(ContentBase):
    id: UUID
    slug: str
    author_id: Optional[UUID] = None
    author_name: Optional[str] = None
    category_id: Optional[UUID] = None
    sub_type: Optional[ContentSubType]
    status: ContentStatus
    published_at: Optional[datetime] = None
    featured: bool
    premium_content: bool
    
    view_count: int
    like_count: int
    bookmark_count: int
    average_rating: Optional[float] = None
    review_count: int
    
    duration: Optional[int] = None # Overall duration (e.g., for audiobooks)
    page_count: Optional[int] = None # Overall page count (e.g., for books)

    # Optionally include chapters in the main content response
    chapters: Optional[List[ContentChapterResponse]] = [] 
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True