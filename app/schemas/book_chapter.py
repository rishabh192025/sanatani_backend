# app/schemas/book_chapter.py
from pydantic import BaseModel, Field, HttpUrl, model_validator
from typing import Optional, List, Any
from pydantic import ValidationInfo
from app.models.content import BookChapter  # Import your SQLAlchemy model
from uuid import UUID
from datetime import datetime
from app.schemas.book_section import BookSectionResponse # Import section schema

class BookChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    #chapter_number: int = Field(..., gt=0)
    description: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None

class BookChapterCreate(BookChapterBase):
    pass

class BookChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None # New field

class BookChapterResponseWithoutSections(BookChapterBase):
    id: UUID
    book_id: UUID
    chapter_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookChapterResponse(BookChapterResponseWithoutSections):
    sections: Optional[List[BookSectionResponse]] = None # Added sections

    class Config:
        from_attributes = True