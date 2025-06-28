# app/schemas/book_toc.py (New File) or add to app/schemas/book_chapter.py
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class TOCSectionItem(BaseModel):
    id: UUID
    title: Optional[str] = None # Section title might be optional
    section_order: int

    class Config:
        from_attributes = True

class TOCChapterItem(BaseModel):
    id: UUID
    title: str
    chapter_number: int
    sections: List[TOCSectionItem] = []
    audio_url: Optional[str] = None

    class Config:
        from_attributes = True

class BookTableOfContentsResponse(BaseModel):
    book_id: UUID
    book_title: str
    chapters: List[TOCChapterItem] = []
    cover_image_url: Optional[str] = None

    class Config:
        from_attributes = True