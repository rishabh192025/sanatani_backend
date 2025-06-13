from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...crud import lost_heritage_crud
from ...schemas import LostHeritageCreate, LostHeritageUpdate, LostHeritageOut, LostHeritageContentType, LostHeritageCategoryType
from ...database import get_async_db

router = APIRouter()


@router.post("", response_model=LostHeritageOut, status_code=status.HTTP_201_CREATED)
async def create_lost_heritage(
    lost_heritage_in: LostHeritageCreate,
    db: AsyncSession = Depends(get_async_db),
):
    existing = await lost_heritage_crud.get_by_title(db, title=lost_heritage_in.title)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Lost Heritage with this title already exists.",
        )
    return await lost_heritage_crud.create(db=db, obj_in=lost_heritage_in)

#TODO: APIs to be created -> 1. for search by title, and other for increasing viewcount

#TODO: for listing on user side no filters are there ask sir after finalizing crud operations do we need filter or leave my opinion leave https://v0-29-may.vercel.app/lost-heritage
"""
User Side:
Display All as no filter give these data or all -> thumbnail img, content_type, category_type, title, description

Admin Side:
Display All give these data or all -> Title, Category, Type, Status, Views, Created_At, for Actions call APIS, view by ID, Edit, Delete
"""

@router.get("", response_model=List[LostHeritageOut])
async def list_all_lost_heritages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all lost heritages.
    """
    lost_heritages = await lost_heritage_crud.get_multi(db=db, skip=skip, limit=limit)
    return lost_heritages


@router.get("/{lost_heritage_id}", response_model=LostHeritageOut)
async def get_lost_heritage(lost_heritage_id: UUID, db: AsyncSession = Depends(get_async_db)):
    lost_heritage = await lost_heritage_crud.get(db=db, id=lost_heritage_id)
    if not lost_heritage:
        raise HTTPException(status_code=404, detail="Lost Heritage not found")
    return lost_heritage


@router.put("/{lost_heritage_id}", response_model=LostHeritageOut)
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