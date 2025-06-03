# app/schemas/content_section.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ContentSectionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    body: str
    section_order: int = Field(default=0, ge=0)

class ContentSectionCreate(ContentSectionBase):
    pass # chapter_id will be path parameter

class ContentSectionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    section_order: Optional[int] = Field(None, ge=0)

class ContentSectionResponse(ContentSectionBase):
    id: UUID
    chapter_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True