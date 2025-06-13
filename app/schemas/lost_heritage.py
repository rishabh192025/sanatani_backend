from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class LostHeritageContentType(str, Enum):
    ARTICLE = "article"
    DOCUMENTARY = "documentary"
    GALLERY = "gallery"

class LostHeritageCategoryType(str, Enum):
    ANCIENT_ART = "ancient_art"
    ANCIENT_TEMPLES = "ancient_temples"
    ARCHAEOLOGICAL_SITES = "archaeological_sites"
    CULTURAL_PRACTICES = "cultural_practices"
    FORGOTTEN_SCRIPTURES = "forgotten_scriptures"
    FORGOTTEN_TRADITIONS = "forgotten_traditions"
    HISTORICAL_ROUTES = "historical_routes"
    LOST_CITIES = "lost_cities"
    LOST_SCRIPTURES = "lost_scriptures"
    SACRED_ARTIFACTS = "sacred_artifacts"
    SACRED_GROVES = "sacred_groves"

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

    is_active: Optional[bool] = True
    is_featured: Optional[bool] = False
    is_published: Optional[bool] = False


class LostHeritageCreate(LostHeritageBase):
    title: str
    content_type: LostHeritageContentType
    category: LostHeritageCategoryType
    category_id: Optional[UUID] = None
    created_by: Optional[UUID] = None


class LostHeritageUpdate(LostHeritageBase):
    title: Optional[str] = None
    content_type: Optional[LostHeritageContentType] = None
    category: Optional[LostHeritageCategoryType] = None
    category_id: Optional[UUID] = None
    created_by: Optional[UUID] = None


class LostHeritageOut(LostHeritageBase):
    id: UUID
    title: Optional[str] = None
    content_type: Optional[LostHeritageContentType] = None
    category: Optional[LostHeritageCategoryType] = None
    category_id: Optional[UUID] = None
    view_count: Optional[int] = 0
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True