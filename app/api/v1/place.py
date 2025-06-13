from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...models.place import State, City, Region
from ...schemas.place import StateResponse, CityResponse, RegionResponse
from sqlalchemy.future import select # Changed for SQLAlchemy 1.4+ style with async
from ...crud import place_crud
from ...schemas import PlaceCreate, PlaceUpdate, PlaceOut, PlaceType
from ...database import get_async_db

router = APIRouter()

# NOTE: Static paths MUST come before dynamic {place_id} path to avoid UUID conflicts.

@router.post("", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_in: PlaceCreate,
    db: AsyncSession = Depends(get_async_db),
):
    existing = await place_crud.get_by_name(db, name=place_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A place with this name already exists.",
        )
    return await place_crud.create(db=db, obj_in=place_in)


@router.get("", response_model=List[PlaceOut])
async def list_places(
    is_featured: Optional[bool] = Query(None),
    category: Optional[PlaceType]= Query(None),
    region: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    return await place_crud.get_filtered(
        db=db,
        is_featured=is_featured,
        category=category.value if category else None,
        region=region,
        state=state,
        country=country,
        skip=skip,
        limit=limit,
    )

# NOTE: These 3 APIs are used to fetch region, state, city in drop down while creating new place

@router.get("/regions", response_model=List[RegionResponse])
async def get_all_regions(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Region))
    regions = result.scalars().all()
    return regions

# @router.get("/regions", response_model=List[RegionResponse])
# def get_all_regions(db: Session = Depends(get_db_sync)):
#     regions = db.query(Region).all()
#     return regions


# @router.get("/regions", response_model=List[RegionResponse])
# async def get_all_regions(
#         skip: int = Query(0, ge=0),
#         limit: int = Query(50, ge=1, le=100),
#         db: AsyncSession = Depends(get_async_db)
# ):
#     result = await db.execute(
#         select(Region)
#         .options(selectinload(Region.states))  # Eager load the relationship
#         .offset(skip)
#         .limit(limit)
#     )
#     regions = result.scalars().all()
#     return regions

@router.get("/regions/{region_id}/states", response_model=List[StateResponse])
async def get_states_by_region(region_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(State).where(State.region_id == region_id))
    states = result.scalars().all()
    return states

# @router.get("/regions/{region_id}/states", response_model=List[StateResponse])
# def get_states_for_region(region_id: UUID, db: Session = Depends(get_db_sync)):
#     states = db.query(State).filter(State.region_id == region_id).all()
#     return states


# @router.get("/regions/{region_id}/states", response_model=List[StateResponse])
# async def get_states_for_region(region_id: UUID, db: AsyncSession = Depends(get_async_db)):
#     # states = await place_crud.get(db=db, id=region_id)
#     # if not states:
#     #     raise HTTPException(status_code=404, detail="States not found")
#     states = await db.query(State).filter(State.region_id == region_id).all()
#     return states

@router.get("/states/{state_id}/cities", response_model=List[CityResponse])
async def get_cities_by_state(state_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(City).where(City.state_id == state_id))
    cities = result.scalars().all()
    return cities


# @router.get("/states/{state_id}/cities", response_model=List[CityResponse])
# def get_cities_for_state(state_id: UUID, db: Session = Depends(get_db_sync)):
#     cities = db.query(City).filter(City.state_id == state_id).all()
#     return cities


@router.get("/{place_id}", response_model=PlaceOut)
async def get_place(place_id: UUID, db: AsyncSession = Depends(get_async_db)):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.put("/{place_id}", response_model=PlaceOut)
async def update_place(
    place_id: UUID,
    place_in: PlaceUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return await place_crud.update(db=db, db_obj=place, obj_in=place_in)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(place_id: UUID, db: AsyncSession = Depends(get_async_db)):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    await place_crud.remove(db=db, id=place_id)
    return
