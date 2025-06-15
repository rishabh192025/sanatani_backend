# app/api/v1/bookmarks.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID as PyUUID

from app.database import get_async_db
from app.schemas.bookmark import BookmarkCreate, BookmarkResponse, BookmarkUpdate
from app.schemas.pagination import PaginatedResponse # Import your pagination schema
from app.crud.bookmark import bookmark_crud
from app.dependencies import get_current_user # User must be logged in
from app.models.user import User

router = APIRouter()
BOOKMARK_TAG = "Bookmarks"

@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED, tags=[BOOKMARK_TAG])
async def create_user_bookmark(
    bookmark_in: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        bookmark = await bookmark_crud.create_bookmark(
            db=db, obj_in=bookmark_in, user_id=current_user.id
        )
        # Eager load content for the response
        await db.refresh(bookmark, attribute_names=['content'])
    except ValueError as e: # Custom errors from CRUD
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError: # From DB unique constraint
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content already bookmarked by this user or invalid content ID."
        )
    return bookmark

@router.get("", response_model=PaginatedResponse[BookmarkResponse], tags=[BOOKMARK_TAG])
async def list_my_bookmarks(
    request: Request,
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    bookmarks, total_count = await bookmark_crud.get_user_bookmarks_paginated(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    
    # Construct next and previous page URLs
    next_page, prev_page = None, None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_page = str(request.url.replace_query_params(**next_params))
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_page = str(request.url.replace_query_params(**prev_params))

    return PaginatedResponse[BookmarkResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=bookmarks # CRUD already eager loads content
    )

@router.get("/{content_id}", response_model=BookmarkResponse, tags=[BOOKMARK_TAG])
async def get_my_bookmark_for_content(
    content_id: PyUUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    bookmark = await bookmark_crud.get_by_user_and_content(
        db=db, user_id=current_user.id, content_id=content_id
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found for this content.")
    await db.refresh(bookmark, attribute_names=['content'])
    return bookmark

@router.put("/{content_id}", response_model=BookmarkResponse, tags=[BOOKMARK_TAG])
async def update_my_bookmark_notes(
    content_id: PyUUID,
    bookmark_in: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    bookmark = await bookmark_crud.get_by_user_and_content(
        db=db, user_id=current_user.id, content_id=content_id
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found for this content to update.")
    
    updated_bookmark = await bookmark_crud.update(db=db, db_obj=bookmark, obj_in=bookmark_in)
    await db.refresh(updated_bookmark, attribute_names=['content'])
    return updated_bookmark

@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[BOOKMARK_TAG])
async def delete_my_bookmark(
    content_id: PyUUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    deleted = await bookmark_crud.remove_bookmark(
        db=db, user_id=current_user.id, content_id=content_id
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found to delete.")
    return