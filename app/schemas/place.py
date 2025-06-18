from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class PlaceBase(BaseModel):
    country_id: Optional[UUID] = None
    region_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    city_id: Optional[UUID] = None

    place_description: Optional[str] = None

    category_id: Optional[UUID] = None
    is_featured: Optional[bool] = False

    religious_importance: Optional[str] = None
    historical_background: Optional[str] = None

    location_description: Optional[str] = None
    latitude: Optional[float] = 0
    longitude: Optional[float] = 0

    cover_image: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    is_active: Optional[bool] = True


class PlaceCreate(PlaceBase):
    name: str


class PlaceUpdate(PlaceBase):
    name: Optional[str] = None


class PlaceResponse(PlaceBase):
    id: UUID
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    class Config:  # Only needed in this as this only involves converting from ORM objects
        from_attributes = True