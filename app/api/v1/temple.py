from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...crud import temple_crud
from ...schemas import TempleCreate, TempleUpdate, TempleResponse
from ...database import get_async_db


router = APIRouter()


@router.post("", response_model=TempleResponse, status_code=status.HTTP_201_CREATED)
async def create_temple(
    temple_in: TempleCreate,
    # current_user: User = Depends(get_current_active_moderator_or_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    existing = await temple_crud.get_by_name(db, name=temple_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Temple with this name already exists.",
        )
    result = await temple_crud.create_temple(
        db=db,
        obj_in=temple_in,
        # created_by = current_user.id,
        created_by = "7e6bacf9-69f5-4807-a8e8-9b961b6c1e51"
    )
    return result


@router.get("", response_model=List[TempleResponse])
async def list_all_temples(
    name: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all Temples if no filters are added else returns the filtered ones.
    Add more filters as needed.
    As of now only from admin side search by name filtered is applied, if required any for user side will add.
    """
    temples = await temple_crud.get_filtered(
        db=db,
        name=name,
        skip=skip,
        limit=limit,
    )
    return temples


@router.get("/{temple_id}", response_model=TempleResponse)
async def get_temple(temple_id: UUID, db: AsyncSession = Depends(get_async_db)):
    temple = await temple_crud.get(db=db, id=temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail="Temple not found")

    temple.visit_count += 1

    await db.commit()       # Commit to make it permanent
    await db.refresh(temple)     # Refresh to re-fetch any auto-updated fields (optional)

    return temple


@router.put("/{temple_id}", response_model=TempleResponse)
async def update_temple(
    temple_id: UUID,
    temple_in: TempleUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    temple = await temple_crud.get(db=db, id=temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail="Temple not found")
    return await temple_crud.update(db=db, db_obj=temple, obj_in=temple_in)


@router.delete("/{temple_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_temple(temple_id: UUID, db: AsyncSession = Depends(get_async_db)):
    temple = await temple_crud.get(db=db, id=temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail="Temple not found")
    await temple_crud.remove(db=db, id=temple_id)
    return