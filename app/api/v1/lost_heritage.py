from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...crud import lost_heritage_crud
from ...schemas import LostHeritageCreate, LostHeritageUpdate, LostHeritageResponse
from ...database import get_async_db


router = APIRouter()


@router.post("", response_model=LostHeritageResponse, status_code=status.HTTP_201_CREATED)
async def create_lost_heritage(
    lost_heritage_in: LostHeritageCreate,
    # current_user: User = Depends(get_current_active_moderator_or_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    existing = await lost_heritage_crud.get_by_title(db, title=lost_heritage_in.title)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Lost Heritage with this title already exists.",
        )
    result = await lost_heritage_crud.create_lost_heritage(
        db=db,
        obj_in=lost_heritage_in,
        # created_by = current_user.id,
        created_by = "7e6bacf9-69f5-4807-a8e8-9b961b6c1e51"
    )
    return result


@router.get("", response_model=List[LostHeritageResponse])
async def list_all_lost_heritages(
    title: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all lost heritages if no filters are added.
    Add more filters as needed.
    """
    lost_heritages = await lost_heritage_crud.get_filtered(
        db=db,
        title=title,
        skip=skip,
        limit=limit,
    )
    return lost_heritages


@router.get("/{lost_heritage_id}", response_model=LostHeritageResponse)
async def get_lost_heritage(lost_heritage_id: UUID, db: AsyncSession = Depends(get_async_db)):
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
    db: AsyncSession = Depends(get_async_db),
):
    lost_heritage = await lost_heritage_crud.get(db=db, id=lost_heritage_id)
    if not lost_heritage:
        raise HTTPException(status_code=404, detail="Lost Heritage not found")
    return await lost_heritage_crud.update(db=db, db_obj=lost_heritage, obj_in=lost_heritage_in)


@router.delete("/{lost_heritage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lost_heritage(lost_heritage_id: UUID, db: AsyncSession = Depends(get_async_db)):
    lost_heritage = await lost_heritage_crud.get(db=db, id=lost_heritage_id)
    if not lost_heritage:
        raise HTTPException(status_code=404, detail="Lost Heritage not found")
    await lost_heritage_crud.remove(db=db, id=lost_heritage_id)
    return