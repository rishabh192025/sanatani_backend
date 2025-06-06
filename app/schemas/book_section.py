# app/schemas/book_section.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class BookSectionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    body: str
    section_order:  Optional[int] = Field(default=0, ge=0)

class BookSectionCreate(BookSectionBase):
    pass # chapter_id will be path parameter

class BookSectionUpdate(BookSectionBase):
    pass

class BookSectionResponse(BookSectionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookSectionUpdatePayload(BaseModel): # A dedicated schema for update payload
    title: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    section_order: Optional[int] = Field(None, ge=0)