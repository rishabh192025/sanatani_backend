# app/api/v1/place.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.crud import place_crud
from app.schemas import PlaceCreate, PlaceUpdate, PlaceResponse, PaginatedResponse
from app.database import get_async_db
from app.dependencies import get_current_active_admin, get_current_user
from app.models.user import User 

router = APIRouter()

# NOTE: Static paths MUST come before dynamic {place_id} path to avoid UUID conflicts.

@router.post("", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_in: PlaceCreate,
    current_user: User = Depends(get_current_active_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    # existing = await place_crud.get_by_name(db, name=place_in.name)
    # if existing:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="A place with this name already exists.",
    #     )
    result = await place_crud.create_place(
        db=db,
        obj_in=place_in,
        # created_by = current_user.id,
        created_by="7e6bacf9-69f5-4807-a8e8-9b961b6c1e51"
        )
    return result


@router.get("", response_model=PaginatedResponse[PlaceResponse])
async def list_places(
    request: Request,  # Add this to build next/prev URLs
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    category_id: Optional[UUID]= Query(None),
    region_id: Optional[UUID]= Query(None),
    state_id: Optional[UUID]= Query(None),
    country_id: Optional[UUID]= Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    places, total_count = await place_crud.get_filtered_with_count(
        db=db,
        skip=skip,
        limit=limit,
        name=name,
        is_featured=is_featured,
        category_id=category_id,
        region_id=region_id,
        state_id=state_id,
        country_id=country_id,
    )
    response_items = [PlaceResponse.model_validate(p) for p in places]

    base_url = str(request.url.remove_query_params(keys=["skip", "limit"]))
    next_page = prev_page = None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_page = str(request.url.replace_query_params(**next_params))
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_page = str(request.url.replace_query_params(**prev_params))

    return PaginatedResponse[PlaceResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: UUID, 
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.put("/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: UUID,
    place_in: PlaceUpdate,
    current_user: User = Depends(get_current_active_admin),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return await place_crud.update(db=db, db_obj=place, obj_in=place_in)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    place_id: UUID, 
    current_user: User = Depends(get_current_active_admin),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    place = await place_crud.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    await place_crud.remove(db=db, id=place_id)
    return
