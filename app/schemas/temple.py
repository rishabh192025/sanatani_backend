from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TempleBase(BaseModel):
    main_deity: Optional[str] = None
    address: Optional[str] = None
    visiting_hours: Optional[str] = None
    description: Optional[str] = None
    history: Optional[str] = None
    architecture: Optional[str] = None
    cover_image: Optional[List[str]] = None
    is_featured: Optional[bool] = False
    is_active: Optional[bool] = True


class TempleCreate(TempleBase):
    place_id: UUID
    name: str


class TempleUpdate(TempleBase):
    place_id: Optional[UUID] = None
    name: Optional[str] = None


class TempleResponse(TempleBase):
    id: UUID
    place_id: Optional[UUID] = None
    place_name: Optional[str] = None
    name: Optional[str] = None
    visit_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    class Config:           # Only needed in this as this only involves converting from ORM objects
        from_attributes = True