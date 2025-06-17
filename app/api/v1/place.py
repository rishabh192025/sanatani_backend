# app/api/v1/place.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...crud import place_crud
from ...schemas import PlaceCreate, PlaceUpdate, PlaceResponse
from ...database import get_async_db

router = APIRouter()

# NOTE: Static paths MUST come before dynamic {place_id} path to avoid UUID conflicts.

@router.post("", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("", response_model=List[PlaceResponse])
async def list_places(
    name: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    category_id: Optional[UUID]= Query(None),
    region_id: Optional[UUID]= Query(None),
    state_id: Optional[UUID]= Query(None),
    country_id: Optional[UUID]= Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    return await place_crud.get_filtered(
        db=db,
        name=name,
        is_featured=is_featured,
        category_id=category_id,
        region_id=region_id,
        state_id=state_id,
        country_id=country_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(place_id: UUID, db: AsyncSession = Depends(get_async_db)):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.put("/{place_id}", response_model=PlaceResponse)
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
