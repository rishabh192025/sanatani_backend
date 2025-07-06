from enum import Enum

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


class DifficultyType(str, Enum):
    EASY = "Easy"
    MODERATE = "Moderate"
    CHALLENGING = "Challenging"
    DIFFICULT = "Difficult"


class DurationType(str, Enum):
    ONE_TO_THREE_DAYS = "1-3 days"
    FOUR_TO_SEVEN_DAYS = "4-7 days"
    ONE_TO_TWO_WEEKS = "1-2 weeks"
    TWO_PLUS_WEEKS = "2+ weeks"


class PilgrimageRouteBase(BaseModel):
    description: Optional[str] = None
    # slug: Optional[str] = None        # not needed from user or as of now show to user, creating internally
    spiritual_significance: Optional[str] = None

    difficulty_level: Optional[DifficultyType] = None
    estimated_duration: Optional[DurationType] = None
    best_season_start: Optional[date] = None
    best_season_end: Optional[date] = None

    itinerary: Optional[str] = None
    route_path: Optional[List[str]] = None      # for this from admin side have to give number of stops

    cover_image: Optional[str] = None
    is_featured: Optional[bool] = False
    view_count: Optional[int] = 0


class PilgrimageRouteCreate(PilgrimageRouteBase):
    name: str
    # category_id: Optional[UUID] = None          # not using as of now


class PilgrimageRouteUpdate(PilgrimageRouteBase):
    name: Optional[str] = None
    # category_id: Optional[UUID] = None


class PilgrimageRouteResponse(PilgrimageRouteBase):
    id: UUID
    # category_id: Optional[UUID] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    class Config:           # Only needed in this as this only involves converting from ORM objects
        from_attributes = True

class PilgrimagePlace(BaseModel):
    id: UUID
    name: str
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0

    class Config:
        from_attributes = True

class PilgrimageRouteResponseWithStops(PilgrimageRouteBase):
    id: UUID
    # category_id: Optional[UUID] = None
    name: Optional[str] = None
    stops: Optional[List[PilgrimagePlace]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True