from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_current_user, get_current_active_admin
from app.models.user import User
from app.crud import chat_with_guruji_crud
from app.schemas import ChatWithGurujiCreate, ChatWithGurujiUpdate, ChatWithGurujiResponse, PaginatedResponse
from app.database import get_async_db


router = APIRouter()


@router.post("", response_model=ChatWithGurujiResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_with_guruji_in: ChatWithGurujiCreate,
    current_user: User = Depends(get_current_user), # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    existing_chat = await chat_with_guruji_crud.get_by_chat_id(db, chat_id=chat_with_guruji_in.chat_id)
    if existing_chat:
        updated_chat = await chat_with_guruji_crud.update(
            db=db,
            db_obj=existing_chat,
            obj_in=chat_with_guruji_in
        )
        return updated_chat

    new_chat = await chat_with_guruji_crud.create_chat_with_guruji(
        db=db,
        obj_in=chat_with_guruji_in,
        user_id = current_user.id
    )
    return new_chat


@router.get("", response_model=PaginatedResponse[ChatWithGurujiResponse])
async def list_all_chats(
    request: Request,  # Add this to build next/prev URLs
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all chats.
    """
    chats, total_count = await chat_with_guruji_crud.get_filtered_with_count(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    response_items = [ChatWithGurujiResponse.model_validate(p) for p in chats]

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

    return PaginatedResponse[ChatWithGurujiResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )


@router.get("/{chat_id}", response_model=ChatWithGurujiResponse)
async def get_chat_by_id(
    chat_id: str,
    current_user: User = Depends(get_current_user),  
    db: AsyncSession = Depends(get_async_db)
):
    chat = await chat_with_guruji_crud.get_by_chat_id(db=db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return chat


@router.put("/{chat_id}", response_model=ChatWithGurujiResponse)
async def update_chat(
    chat_id: str,
    chat_with_guruji_in: ChatWithGurujiUpdate,
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    chat = await chat_with_guruji_crud.get_by_chat_id(db=db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return await chat_with_guruji_crud.update(db=db, db_obj=chat, obj_in=chat_with_guruji_in)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str, 
    current_user: User = Depends(get_current_user),  
    db: AsyncSession = Depends(get_async_db)
):
    chat = await chat_with_guruji_crud.get_by_chat_id(db=db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    await chat_with_guruji_crud.delete_chat(db=db, chat_id=chat_id)
    return