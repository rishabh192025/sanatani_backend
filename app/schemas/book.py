# app/schemas/book.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.content import ContentType, ContentStatus, LanguageCode, ContentSubType, BookType # Import enums
from app.schemas.book_chapter import BookChapterResponse



class BookBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    language: str = LanguageCode.EN.value
    tags: Optional[List[str]] = Field(None, max_items=20)
    cover_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_url: Optional[str] = None 

class BookCreate(BookBase):
    category_id: Optional[str] = None # Assuming category ID is passed as string UUID
    premium_content: bool = False
    author_name: Optional[str] = Field(None, max_length=200) 
    status: Optional[str] = ContentStatus.PUBLISHED.value
    featured: Optional[bool] = False
    book_type : Optional[BookType] = BookType.TEXT

class BookUpdate(BaseModel): # Does not inherit BookBase
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = Field(None, max_items=20)
    cover_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_url: Optional[str] = None
    category_id: Optional[str] = None
    premium_content: Optional[bool] = None # Only one premium_content
    author_name: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = ContentStatus.PUBLISHED.value # Make status optional for update
    featured: Optional[bool] = None

class BookResponse(BookBase):
    id: UUID
    slug: str
    author_name: Optional[str] = None
    category_id: Optional[UUID] = None # Or UUID if you prefer consistency with id
    book_format: Optional[str] = None # e.g., "TEXT", "AUDIO", "PDF"
    status: str
    published_at: Optional[datetime] = None
    featured: bool
    premium_content: bool
    view_count: int
    like_count: int
    bookmark_count: int
    average_rating: Optional[float] = None
    review_count: int
    page_count: Optional[int] = None
    duration: Optional[int] = None # Useful for audio books
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
