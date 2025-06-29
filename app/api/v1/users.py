# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_async_db, get_current_user, get_current_active_admin
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.crud.user import user_crud
from app.models.user import User

router = APIRouter()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin) # Optional: only admins can create users
):
    """
    Create a new user.
    Consider if this should be public or admin-only (like registration).
    Registration is typically public, so this might be for admin creation.
    If for registration, it should likely be in auth.py or a public user endpoint.
    For now, assuming admin creation or it will be moved to auth.py.
    """
    existing_user = await user_crud.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    if user_in.username:
        existing_username = await user_crud.get_user_by_username(db, username=user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken.",
            )
    
    user = await user_crud.create_user(db=db, obj_in=user_in)
    return user


@router.get("", response_model=List[UserResponse])
async def read_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    #current_admin: User = Depends(get_current_active_admin) # Only admins can list all users
):
    """
    Retrieve all users. Admin access required.
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserResponse)
async def read_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get profile of the current logged-in user. (This is also in auth.py, decide where it fits best)
    It's common to have it in users.py as /users/me and auth.py might have /auth/me
    or just one /me endpoint. For now, keeping it here.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update profile of the current logged-in user.
    """
    # user_crud.update expects db_obj and obj_in.
    # We need to pass the current_user (which is the db_obj)
    updated_user = await user_crud.update_user(db=db, db_obj=current_user, obj_in=user_in)
    return updated_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Or get_current_active_admin for stricter access
):
    """
    Get a specific user by ID.
    Admins can get any user. Regular users might only get their own (covered by /me).
    """
    if current_user.role != "admin" and current_user.id != user_id: # Using string role for now
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    user = await user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: UUID,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin) # Only admins can update other users
):
    """
    Update a user by ID. Admin access required.
    """
    db_user = await user_crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Prevent admin from accidentally changing their own role via this endpoint if not careful
    if db_user.id == current_admin.id and user_in.role and user_in.role != current_admin.role:
         if user_in.role != "admin": # Or any other logic for self-role change
            raise HTTPException(status_code=400, detail="Admin cannot demote themselves via this endpoint.")

    updated_user = await user_crud.update_user(db=db, db_obj=db_user, obj_in=user_in)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin) # Only admins can delete users
):
    """
    Delete a user by ID. Admin access required.
    Consider soft delete.
    """
    db_user = await user_crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if db_user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin cannot delete themselves.")
    
    await user_crud.remove(db=db, id=user_id)
    return # No content