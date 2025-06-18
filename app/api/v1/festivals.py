# app/api/v1/festivals.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID as PyUUID

from app.crud.festival import festival_crud
from app.schemas.festival import FestivalCreate, FestivalUpdate, FestivalResponse
from app.schemas.pagination import PaginatedResponse # Import your pagination schema
from app.database import get_async_db
from app.dependencies import get_current_user # Assuming authentication
from app.models.user import User # For type hinting

router = APIRouter()
FESTIVAL_TAG = "Hindu Festivals"

@router.post("", response_model=FestivalResponse, status_code=status.HTTP_201_CREATED, tags=[FESTIVAL_TAG])
async def create_new_festival(
    festival_in: FestivalCreate,
    db: AsyncSession = Depends(get_async_db),
    #current_user: User = Depends(get_current_user) # Ensure user is authenticated
):
    # TODO: Add role-based permission if needed (e.g., only admins/moderators can create)
    # from app.dependencies import get_current_active_moderator_or_admin
    # current_user: User = Depends(get_current_active_moderator_or_admin)
    
    # Ensure the state_id provided exists (optional, FK constraint will catch it)
    # from app.crud.location_geo import state_crud # Assuming state_crud
    # state = await state_crud.get(db, id=festival_in.state_id)
    # if not state:
    #     raise HTTPException(status_code=400, detail=f"State with ID {festival_in.state_id} not found.")

    try:
        festival = await festival_crud.create_festival(
            db=db, 
            obj_in=festival_in, 
            created_by_id="1f3d72a7-f5cf-4200-8300-77c13cad6117"
            #created_by_id=current_user.id
        )
    except ValueError as e: # Your pre-check
        print(f"API caught ValueError: {e}") # Log this
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e_db: # DB constraint violation
        print(f"API caught IntegrityError: {e_db}") # Log this
        await db.rollback() 
        # Check the specific error code/message if possible to confirm it's a unique constraint violation
        # For psycopg, unique_violation is '23505'
        # if hasattr(e_db.orig, 'pgcode') and e_db.orig.pgcode == '23505':
        #     detail_msg = f"A festival with the name '{festival_in.name}' already exists (database constraint)."
        # else:
        #     detail_msg = "Database integrity error."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail=f"A festival with the name '{festival_in.name}' already exists (database constraint).")
    return festival


@router.get("", response_model=PaginatedResponse[FestivalResponse], tags=[FESTIVAL_TAG])
async def list_all_festivals(
    request: Request, # For pagination URLs
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    state_id: Optional[PyUUID] = Query(None, description="Filter by State ID"),
    # category_id: Optional[PyUUID] = Query(None, description="Filter by Category ID"),
    is_major: Optional[bool] = Query(None, description="Filter by major festivals"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    is_active: Optional[bool] = Query(True, description="Filter by active status (defaults to True)"),
    db: AsyncSession = Depends(get_async_db),
):
    festivals, total_count = await festival_crud.get_festivals_paginated(
        db=db, skip=skip, limit=limit, state_id=state_id, # category_id=category_id,
        is_major=is_major, search_query=search, is_active=is_active
    )

    # Construct pagination URLs
    next_page, prev_page = None, None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_page = str(request.url.replace_query_params(**next_params))
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_page = str(request.url.replace_query_params(**prev_params))
        
    return PaginatedResponse[FestivalResponse](
        total_count=total_count, limit=limit, skip=skip, 
        items=festivals, next_page=next_page, prev_page=prev_page
    )


@router.get("/{festival_id}", response_model=FestivalResponse, tags=[FESTIVAL_TAG])
async def get_single_festival(
    festival_id: PyUUID, 
    db: AsyncSession = Depends(get_async_db)
):
    festival = await festival_crud.get(db=db, id=festival_id) # CRUDBase get
    if not festival or not festival.is_active: # Also check if active for public view
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festival not found or not active")
    # await db.refresh(festival, attribute_names=['state']) # If you want to include state details
    return festival


@router.put("/{festival_id}", response_model=FestivalResponse, tags=[FESTIVAL_TAG])
async def update_existing_festival(
    festival_id: PyUUID,
    festival_in: FestivalUpdate,
    db: AsyncSession = Depends(get_async_db),
    #current_user: User = Depends(get_current_user) # Or a more privileged user
):
    db_festival = await festival_crud.get(db=db, id=festival_id)
    if not db_festival:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festival not found")

    # TODO: Permission check: only creator or admin/moderator can update
    # if db_festival.created_by_id != current_user.id and current_user.role not in [UserRole.ADMIN.value, UserRole.MODERATOR.value]:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    try:
        updated_festival = await festival_crud.update_festival(db=db, db_obj=db_festival, obj_in=festival_in)
    except ValueError as e: # From CRUD for name conflict
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    # await db.refresh(updated_festival, attribute_names=['state'])
    return updated_festival


@router.delete("/{festival_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[FESTIVAL_TAG])
async def delete_existing_festival(
    festival_id: PyUUID, 
    db: AsyncSession = Depends(get_async_db),
    #current_user: User = Depends(get_current_user) # Or get_current_active_admin
):
    db_festival = await festival_crud.get(db=db, id=festival_id)
    if not db_festival:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festival not found")

    # TODO: Permission check: only admin or creator can delete
    # if current_user.role != UserRole.ADMIN.value and db_festival.created_by_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this festival")
    
    # Soft delete:
    # db_festival.is_active = False
    # db.add(db_festival)
    # await db.commit()
    # OR Hard delete:
    await festival_crud.remove(db=db, id=festival_id)
    return