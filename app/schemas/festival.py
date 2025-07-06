# app/schemas/festival.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime # Use datetime directly from datetime module
from uuid import UUID

class FestivalBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    alternate_names: Optional[Dict[str, str]] = None # e.g. {"lang_code": "name"}
    description: Optional[str] = None
    significance: Optional[str] = None
    rituals_and_observances: Optional[str] = None
    deities_associated: Optional[List[str]] = None
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: Optional[int] = Field(None, ge=1)
    
    primary_tithi: Optional[str] = None
    primary_nakshatra: Optional[str] = None
    hindu_month: Optional[str] = None
    paksha: Optional[str] = None

    state_id: Optional[UUID] = None # "State is must" - client must provide state ID
    
    # category_id: Optional[UUID] = None
    images: Optional[List[HttpUrl]] = None # Validate as URLs
    is_major_festival: Optional[bool] = False

class FestivalCreate(FestivalBase):
    pass # created_by_id will be handled by the API from the current user

class FestivalUpdate(BaseModel): # More granular updates
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    alternate_names: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    significance: Optional[str] = None
    rituals_and_observances: Optional[str] = None
    deities_associated: Optional[List[str]] = None
    
    gregorian_start_date: Optional[datetime] = None
    gregorian_end_date: Optional[datetime] = None
    duration_days: Optional[int] = Field(None, ge=1)
    
    primary_tithi: Optional[str] = None
    primary_nakshatra: Optional[str] = None
    hindu_month: Optional[str] = None
    paksha: Optional[str] = None

    # state_id: Optional[UUID] = None # Usually, state association doesn't change once set. If it can, add it.
    
    # category_id: Optional[UUID] = None
    images: Optional[List[HttpUrl]] = None
    is_major_festival: Optional[bool] = None


class FestivalResponse(FestivalBase):
    id: UUID
    # To include state name, you'd fetch it in CRUD and add a field here, or have a nested StateResponse
    # state: Optional[StateMinimalResponse] = None 
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID
    # creator_username: Optional[str] = None # Could be added by joining in CRUD

    class Config:
        from_attributes = True # Pydantic v2
        # orm_mode = True # Pydantic v1

# Example for StateMinimalResponse if you want to nest it (define in appropriate geo schemas file)
# class StateMinimalResponse(BaseModel):
#     id: UUID
#     name: str
#     class Config:
#         from_attributes = True