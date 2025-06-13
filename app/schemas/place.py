from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class PlaceType(str, Enum):
    TEMPLES = "temples"
    MOUNTAINS = "mountains"
    RIVERS = "rivers"


class PlaceBase(BaseModel):
    region: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

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
    category: PlaceType
    created_by: Optional[UUID] = None


class PlaceUpdate(PlaceBase):
    name: Optional[str] = None
    category: Optional[PlaceType] = None


class PlaceOut(PlaceBase):
    id: UUID
    name: Optional[str] = None
    category: Optional[PlaceType] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    class Config:
        orm_mode = True


class CityResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True


class StateResponse(BaseModel):
    id: UUID
    name: str
    # cities: list[CityResponse] = None

    class Config:
        orm_mode = True


class RegionResponse(BaseModel):
    id: UUID
    name: str
    # states: list[StateResponse] = None

    class Config:
        orm_mode = True