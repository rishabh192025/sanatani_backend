from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_current_user, get_current_active_admin
from app.models.user import User
from app.crud import temple_crud, place_crud
from app.schemas import TempleCreate, TempleUpdate, TempleResponse, PaginatedResponse
from app.database import get_async_db


router = APIRouter()


@router.post("", response_model=TempleResponse, status_code=status.HTTP_201_CREATED)
async def create_temple(
    temple_in: TempleCreate,
    current_user: User = Depends(get_current_active_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    # existing = await temple_crud.get_by_name(db, name=temple_in.name)
    # if existing:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="A Temple with this name already exists.",
    #     )
    result = await temple_crud.create_temple(
        db=db,
        obj_in=temple_in,
        created_by = current_user.id,
        #created_by = "7e6bacf9-69f5-4807-a8e8-9b961b6c1e51"
    )
    return result


@router.get("", response_model=PaginatedResponse[TempleResponse])
async def list_all_temples(
    request: Request,  # Add this to build next/prev URLs
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all Temples if no filters are added else returns the filtered ones.
    Add more filters as needed.
    As of now only from admin side search by name filtered is applied, if required any for user side will add.
    """
    temples, total_count = await temple_crud.get_filtered_with_count(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
    )
    response_items = [TempleResponse.model_validate(p) for p in temples]
    for idx, res in enumerate(response_items):
        # print(res)
        place= await place_crud.get(db, res.place_id)
        # print(place)
        response_items[idx].place_name = place.name

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

    return PaginatedResponse[TempleResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )


@router.get("/{temple_id}", response_model=TempleResponse)
async def get_temple(
    temple_id: UUID, 
    current_user: User = Depends(get_current_user),  
    db: AsyncSession = Depends(get_async_db)
):
    temple = await temple_crud.get(db=db, id=temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail="Temple not found")

    temple.visit_count += 1

    await db.commit()       # Commit to make it permanent
    await db.refresh(temple)     # Refresh to re-fetch any auto-updated fields (optional)
    # print(temple)
    res = TempleResponse.model_validate(temple)
    # print(res)
    place = await place_crud.get(db, temple.place_id)
    # print(place)
    res.place_name = place.name
    return res


@router.put("/{temple_id}", response_model=TempleResponse)
async def update_temple(
    temple_id: UUID,
    temple_in: TempleUpdate,
    current_user: User = Depends(get_current_active_admin),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    temple = await temple_crud.get(db=db, id=temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail="Temple not found")
    return await temple_crud.update(db=db, db_obj=temple, obj_in=temple_in)


@router.delete("/{temple_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_temple(
    temple_id: UUID, 
    current_user: User = Depends(get_current_active_admin),  
    db: AsyncSession = Depends(get_async_db)
):
    temple = await temple_crud.get(db=db, id=temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail="Temple not found")
    await temple_crud.remove(db=db, id=temple_id)
    return