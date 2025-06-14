from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from sqlalchemy.future import select # Changed for SQLAlchemy 1.4+ style with async
from ...database import get_async_db
from ...models.location import Region, State, City, Country
from ...schemas.location import RegionResponse, StateResponse, CityResponse, CountryResponse


router = APIRouter()

# These APIs are used to fetch country, region, state, city in drop down while creating new place, temple, etc.


@router.get("/countries", response_model=List[CountryResponse])
async def get_all_countries(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Country))
    countries = result.scalars().all()
    return countries


@router.get("/countries/{country_id}/regions", response_model=List[RegionResponse])
async def get_all_regions(country_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Region).where(Region.country_id == country_id))
    states = result.scalars().all()
    return states


@router.get("/regions/{region_id}/states", response_model=List[StateResponse])
async def get_states_by_region(region_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(State).where(State.region_id == region_id))
    states = result.scalars().all()
    return states


@router.get("/states/{state_id}/cities", response_model=List[CityResponse])
async def get_cities_by_state(state_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(City).where(City.state_id == state_id))
    cities = result.scalars().all()
    return cities
