# app/api/routes/sacred_places.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...crud import sacred_place_crud
from ...schemas import SacredPlaceCreate, SacredPlaceUpdate, SacredPlaceOut, PlaceType
from ...database import get_async_db

router = APIRouter()


@router.post("", response_model=SacredPlaceOut, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_in: SacredPlaceCreate,
    db: AsyncSession = Depends(get_async_db),
):
    existing = await sacred_place_crud.get_by_name(db, name=place_in.place_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A place with this name already exists.",
        )
    return await sacred_place_crud.create(db=db, obj_in=place_in)


@router.get("", response_model=List[SacredPlaceOut])
async def list_places(
    country: Optional[str] = Query(None),
    place_type: Optional[PlaceType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    return await sacred_place_crud.get_filtered(
        db=db,
        country=country,
        place_type=place_type.value if place_type else None,
        skip=skip,
        limit=limit,
    )


@router.get("/{place_id}", response_model=SacredPlaceOut)
async def get_place(place_id: UUID, db: AsyncSession = Depends(get_async_db)):
    place = await sacred_place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.put("/{place_id}", response_model=SacredPlaceOut)
async def update_place(
    place_id: UUID,
    place_in: SacredPlaceUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    place = await sacred_place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return await sacred_place_crud.update(db=db, db_obj=place, obj_in=place_in)

@router.patch("/{place_id}", response_model=SacredPlaceOut)
async def update_place(
    place_id: UUID,
    place_in: SacredPlaceUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    place = await sacred_place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return await sacred_place_crud.update(db=db, db_obj=place, obj_in=place_in)

@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(place_id: UUID, db: AsyncSession = Depends(get_async_db)):
    place = await sacred_place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    await sacred_place_crud.remove(db=db, id=place_id)
    return
