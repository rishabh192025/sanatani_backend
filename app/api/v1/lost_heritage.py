from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.dependencies import get_current_active_admin, get_current_user
from app.crud import lost_heritage_crud
from app.schemas import LostHeritageCreate, LostHeritageUpdate, LostHeritageResponse, PaginatedResponse
from app.database import get_async_db
from app.models import User  # Ensure User model is imported for type hinting


router = APIRouter()


@router.post("", response_model=LostHeritageResponse, status_code=status.HTTP_201_CREATED)
async def create_lost_heritage(
    lost_heritage_in: LostHeritageCreate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db),
):
    # existing = await lost_heritage_crud.get_by_title(db, title=lost_heritage_in.title)
    # if existing:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="A Lost Heritage with this title already exists.",
    #     )
    result = await lost_heritage_crud.create_lost_heritage(
        db=db,
        obj_in=lost_heritage_in,
        # created_by = current_user.id,
        created_by = "7e6bacf9-69f5-4807-a8e8-9b961b6c1e51"
    )
    return result


@router.get("", response_model=PaginatedResponse[LostHeritageResponse])
async def list_all_lost_heritages(
    request: Request,
    title: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all lost heritages if no filters are added.
    Add more filters as needed.
    """
    lost_heritages, total_count = await lost_heritage_crud.get_filtered_with_count(
        db=db,
        title=title,
        skip=skip,
        limit=limit,
    )
    response_items = [LostHeritageResponse.model_validate(p) for p in lost_heritages]

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

    return PaginatedResponse[LostHeritageResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )


@router.get("/{lost_heritage_id}", response_model=LostHeritageResponse)
async def get_lost_heritage(
    lost_heritage_id: UUID, 
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    lost_heritage = await lost_heritage_crud.get(db=db, id=lost_heritage_id)
    if not lost_heritage:
        raise HTTPException(status_code=404, detail="Lost Heritage not found")

    lost_heritage.view_count += 1

    await db.commit()       # Commit to make it permanent
    await db.refresh(lost_heritage)     # Refresh to re-fetch any auto-updated fields (optional)

    return lost_heritage


@router.put("/{lost_heritage_id}", response_model=LostHeritageResponse)
async def update_lost_heritage(
    lost_heritage_id: UUID,
    lost_heritage_in: LostHeritageUpdate,
    current_user: User = Depends(get_current_active_admin),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    lost_heritage = await lost_heritage_crud.get(db=db, id=lost_heritage_id)
    if not lost_heritage:
        raise HTTPException(status_code=404, detail="Lost Heritage not found")
    return await lost_heritage_crud.update(db=db, db_obj=lost_heritage, obj_in=lost_heritage_in)


@router.delete("/{lost_heritage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lost_heritage(
    lost_heritage_id: UUID, 
    current_user: User = Depends(get_current_active_admin),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    lost_heritage = await lost_heritage_crud.get(db=db, id=lost_heritage_id)
    if not lost_heritage:
        raise HTTPException(status_code=404, detail="Lost Heritage not found")
    await lost_heritage_crud.remove(db=db, id=lost_heritage_id)
    return