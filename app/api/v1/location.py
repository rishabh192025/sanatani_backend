from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from sqlalchemy.future import select # Changed for SQLAlchemy 1.4+ style with async
from app.database import get_async_db
from app.models.location import Region, State, City, Country
from app.schemas.location import RegionResponse, StateResponse, CityResponse, CountryResponse


router = APIRouter()

# These APIs are used to fetch country, region, state, city in drop down while creating new place, temple, etc.


@router.get("/countries", response_model=List[CountryResponse])
async def get_all_countries(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Country))
    countries = result.scalars().all()
    return countries


@router.get("/countries/regions", response_model=List[RegionResponse])
async def get_all_regions(
    country_id: UUID = Query(default=UUID("ed2cff2f-6065-4a63-a921-73b2af99a0b9"), description="ID of the country to fetch regions for"),
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(Region).where(Region.country_id == country_id))
    states = result.scalars().all()
    return states


@router.get("/regions", response_model=List[RegionResponse])
async def get_all_regions(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Region))
    regions = result.scalars().all()
    return regions


@router.get("/regions/{region_id}/states", response_model=List[StateResponse])
async def get_states_by_region(region_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(State).where(State.region_id == region_id))
    states = result.scalars().all()
    return states


@router.get("/states", response_model=List[StateResponse])
async def get_all_states(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(State))
    states = result.scalars().all()
    return states


@router.get("/states/{state_id}/cities", response_model=List[CityResponse])
async def get_cities_by_state(state_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(City).where(City.state_id == state_id))
    cities = result.scalars().all()
    return cities


@router.get("/cities", response_model=List[CityResponse])
async def get_all_cities(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(City))
    cities = result.scalars().all()
    return cities