# app/api/v1/stories.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.story import StoryCreate, StoryUpdate, StoryResponse

from app.schemas.pagination import PaginatedResponse
from app.crud.story import story_crud
from app.models.user import User
from app.models.content import ContentStatus
from app.dependencies import get_async_db, get_current_user, get_current_active_admin
from uuid import UUID as PyUUID


router = APIRouter()
STORY_TAG = "Stories"

@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED, tags=[STORY_TAG])
async def create_new_story_api(
    story_in: StoryCreate, # Using StoryCreate
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    story = await story_crud.create_story(
        db=db, 
        obj_in=story_in, 
        #author_id="1f3d72a7-f5cf-4200-8300-77c13cad6117"
        author_id=current_user.id
        )
    return story # Pydantic will convert Content model to StoryResponse

@router.get("", response_model=PaginatedResponse[StoryResponse], tags=[STORY_TAG])
async def list_all_stories_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None), # Allow filtering by status
    category_id: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user), # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    # Default to published if no status_filter is provided for public listing
    final_status_str = status_filter if status_filter else ContentStatus.PUBLISHED.value

    story_models, total_count = await story_crud.get_stories_list_and_count(
        db, skip=skip, limit=limit, status_str=final_status_str,
        category_id_str=category_id, language_str=language, search_query=search
    )
    
    response_items = [StoryResponse.model_validate(story) for story in story_models]

    # ... (pagination next/prev page logic) ...
    next_page, prev_page = None, None # Placeholder
    base_url = str(request.url.remove_query_params(keys=['skip', 'limit']))
    if (skip + limit) < total_count:
        next_page_url_params = request.query_params._dict.copy()
        next_page_url_params["skip"] = str(skip + limit)
        next_page = str(request.url.replace_query_params(**next_page_url_params))
    if skip > 0:
        prev_page_url_params = request.query_params._dict.copy()
        prev_page_url_params["skip"] = str(max(0, skip - limit))
        prev_page = str(request.url.replace_query_params(**prev_page_url_params))

    return PaginatedResponse[StoryResponse](
        total_count=total_count, limit=limit, skip=skip, 
        next_page=next_page, prev_page=prev_page, items=response_items
    )

@router.get("/{story_id_or_slug}", response_model=StoryResponse, tags=[STORY_TAG])
async def get_single_story_api(
    story_id_or_slug: str,
    current_user: User = Depends(get_current_user), # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    story_model = None
    try:
        story_uuid = PyUUID(story_id_or_slug)
        story_model = await story_crud.get_story(db, story_id=story_uuid)
    except ValueError:
        story_model = await story_crud.get_story_by_slug(db, slug=story_id_or_slug)
    
    if not story_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return story_model # Pydantic converts Content model to StoryResponse

@router.put("/{story_id}", response_model=StoryResponse, tags=[STORY_TAG])
async def update_existing_story_api(
    story_id: PyUUID,
    story_in: StoryUpdate, # Using StoryUpdate
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    db_story = await story_crud.get_story(db, story_id=story_id)
    if not db_story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    
    # ... (Permission check) ...
    # is_admin_or_moderator = current_user.role in [UserRole.ADMIN.value, UserRole.MODERATOR.value]
    # is_author = db_story.author_id == current_user.id if db_story.author_id else False
    # if not (is_admin_or_moderator or is_author):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
    updated_story = await story_crud.update_story(db=db, db_obj=db_story, obj_in=story_in)
    return updated_story # Pydantic converts

@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[STORY_TAG])
async def delete_existing_story_api(
    story_id: PyUUID,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    db_story = await story_crud.get_story(db, story_id=story_id)
    if not db_story: # Ensure it's actually a story before deleting
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    
    await story_crud.remove(db=db, id=story_id) # Generic remove from CRUDBase
    return