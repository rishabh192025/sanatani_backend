# app/schemas/book_chapter.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.book_section import BookSectionResponse # Import section schema

class BookChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    chapter_number: int = Field(..., gt=0)
    description: Optional[str] = None

class BookChapterCreate(BookChapterBase):
    pass

class BookChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    chapter_number: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None # New field

class BookChapterResponse(BookChapterBase):
    id: UUID
    book_id: UUID
    sections: Optional[List[BookSectionResponse]] = [] # Added sections
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True