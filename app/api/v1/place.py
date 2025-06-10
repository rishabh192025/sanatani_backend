from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...crud import place_crud
from ...schemas import PlaceCreate, PlaceUpdate, PlaceOut, PlaceType
from ...database import get_async_db

router = APIRouter()


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
