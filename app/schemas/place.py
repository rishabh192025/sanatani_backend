from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Union
from enum import Enum
from datetime import datetime


class PlaceType(str, Enum):
    temple = "temple"
    mountain = "mountain"
    river = "river"
    site = "site"
    featured_place = "featured_place"
    historical_site = "historical_site"
    # Add as needed


class SacredPlaceBase(BaseModel):
    place_name: str
    alternate_names: Optional[List[str]] = None
    categories: PlaceType

    region: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    place_description: Optional[str] = None

    latitude: Optional[float] = 0
    longitude: Optional[float] = 0
    elevation: Optional[float] = 0
    location_description: Optional[str] = None

    historical_background: Optional[str] = None
    religious_importance: Optional[str] = None
    legends_stories: Optional[str] = None

    deity_names: Optional[List[str]] = None
    architectural_style: Optional[str] = None
    built_year: Optional[int] = None
    built_century: Optional[str] = None
    dynasty_period: Optional[str] = None

    visiting_hours: Optional[Dict[str, Union[str, int, List]]] = None
    entry_fee: Optional[Dict[str, Union[str, int, float]]] = None
    dress_code: Optional[str] = None
    special_rituals: Optional[Dict[str, Union[str, int, List]]] = None
    festivals_celebrated: Optional[List[str]] = None

    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None

    verification_status: Optional[str] = "pending"
    is_active: Optional[bool] = True
    accessibility_info: Optional[Dict[str, Union[str, int, List]]] = None

    visit_count: Optional[int] = 0
    rating: Optional[float] = 0
    review_count: Optional[int] = 0


class SacredPlaceCreate(SacredPlaceBase):
    pass


class SacredPlaceUpdate(BaseModel):
    place_name: Optional[str] = None
    alternate_names: Optional[List[str]] = None
    categories: Optional[PlaceType] = None

    region: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    place_description: Optional[str] = None

    latitude: Optional[float] = 0
    longitude: Optional[float] = 0
    elevation: Optional[float] = 0
    location_description: Optional[str] = None

    historical_background: Optional[str] = None
    religious_importance: Optional[str] = None
    legends_stories: Optional[str] = None

    deity_names: Optional[List[str]] = None
    architectural_style: Optional[str] = None
    built_year: Optional[int] = None
    built_century: Optional[str] = None
    dynasty_period: Optional[str] = None

    visiting_hours: Optional[Dict[str, Union[str, int, List]]] = None
    entry_fee: Optional[Dict[str, Union[str, int, float]]] = None
    dress_code: Optional[str] = None
    special_rituals: Optional[Dict[str, Union[str, int, List]]] = None
    festivals_celebrated: Optional[List[str]] = None

    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None

    verification_status: Optional[str] = None
    is_active: Optional[bool] = None
    accessibility_info: Optional[Dict[str, Union[str, int, List]]] = None

    visit_count: Optional[int] = 0
    rating: Optional[float] = 0
    review_count: Optional[int] = 0


class SacredPlaceOut(SacredPlaceBase):
    id: UUID4
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID4] = None

    class Config:
        orm_mode = True
