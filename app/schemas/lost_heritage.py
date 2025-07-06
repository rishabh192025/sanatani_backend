from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class LostHeritageContentType(str, Enum):
    ARTICLE = "article"
    DOCUMENTARY = "documentary"
    GALLERY = "gallery"


class LostHeritageBase(BaseModel):
    description: Optional[str] = None

    article_content: Optional[str] = None
    video_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None

    location: Optional[str] = None
    time_period: Optional[str] = None
    historical_significance: Optional[str] = None
    current_status: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

    thumbnail_image: Optional[List[str]] = None

    is_featured: Optional[bool] = False
    is_published: Optional[bool] = False

class LostHeritageCreate(LostHeritageBase):
    title: str
    content_type: LostHeritageContentType
    category_id: Optional[UUID] = None

class LostHeritageUpdate(LostHeritageBase):
    title: Optional[str] = None
    content_type: Optional[LostHeritageContentType] = None
    category_id: Optional[UUID] = None


class LostHeritageResponse(LostHeritageBase):
    id: UUID
    title: Optional[str] = None
    content_type: Optional[LostHeritageContentType] = None
    category_id: Optional[UUID] = None          # sending ID as of now, will later send CategoryResponse if needed
    view_count: Optional[int] = 0
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:           # Only needed in this as this only involves converting from ORM objects
        from_attributes = True