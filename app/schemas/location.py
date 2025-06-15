from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class CountryResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True


class RegionResponse(BaseModel):
    id: UUID
    name: str
    # states: list[StateResponse] = None

    class Config:
        orm_mode = True


class StateResponse(BaseModel):
    id: UUID
    name: str
    # cities: list[CityResponse] = None

    class Config:
        orm_mode = True


class CityResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True