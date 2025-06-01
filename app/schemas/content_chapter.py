# app/schemas/content_chapter.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class ContentChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    chapter_number: int = Field(..., gt=0)
    content_body: Optional[str] = None
    audio_url: Optional[HttpUrl] = None
    video_url: Optional[HttpUrl] = None
    duration: Optional[int] = Field(None, ge=0, description="Duration in seconds")
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    is_preview_allowed: bool = False

class ContentChapterCreate(ContentChapterBase):
    pass # content_id will be path parameter

class ContentChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    chapter_number: Optional[int] = Field(None, gt=0)
    content_body: Optional[str] = None
    audio_url: Optional[HttpUrl] = None
    video_url: Optional[HttpUrl] = None
    duration: Optional[int] = Field(None, ge=0)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    is_preview_allowed: Optional[bool] = None

class ContentChapterResponse(ContentChapterBase):
    id: UUID
    content_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True