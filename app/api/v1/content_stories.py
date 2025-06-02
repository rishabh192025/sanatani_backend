# app/api/v1/content.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID as PyUUID

from app.database import get_async_db
from app.schemas.content import ContentCreate, ContentResponse, ContentUpdate
from app.schemas.content_chapter import ( # Import chapter schemas
    ContentChapterCreate, ContentChapterResponse, ContentChapterUpdate
)
from app.schemas.content_section import ( # Import section schemas
    ContentSectionCreate, ContentSectionResponse, ContentSectionUpdate
)
from app.crud.content_section import content_section_crud # Import section CRUD
from app.crud.content import content_crud
from app.crud.content_chapter import content_chapter_crud # Import chapter CRUD
from app.dependencies import get_current_user, get_current_active_moderator_or_admin, get_current_active_admin
from app.models.user import User
from app.models.content import Content, ContentStatus, ContentType, ContentSubType # For type hinting
from app.services.file_service import file_service

router = APIRouter()

# --- Specific Endpoints for Stories ---
STORY_TAG = "Stories"

@router.get("/stories/", response_model=List[ContentResponse], tags=[STORY_TAG])
async def get_all_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    # Add other relevant filters like language, category if needed
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a list of content items specifically marked as Stories.
    """
    stories = await content_crud.get_content_list(
        db=db,
        skip=skip,
        limit=limit,
        sub_type_str=ContentSubType.STORY.value, # Filter by sub_type
        status_str=ContentStatus.PUBLISHED.value # Default to published
    )
    return stories

@router.get("/stories/{story_id_or_slug}", response_model=ContentResponse, tags=[STORY_TAG])
async def get_single_story(
    story_id_or_slug: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific story by its UUID or slug.
    """
    story: Optional[Content] = None
    try:
        # Try to interpret as UUID first
        story_uuid = PyUUID(story_id_or_slug)
        story = await content_crud.get_content(db=db, content_id=story_uuid, sub_type_str=ContentSubType.STORY.value)
    except ValueError:
        # If not a valid UUID, assume it's a slug
        story = await content_crud.get_content_by_slug(db=db, slug=story_id_or_slug, sub_type_str=ContentSubType.STORY.value)
    
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    
    return story

@router.post("/stories/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED, tags=[STORY_TAG])
async def create_new_story(
    story_in: ContentCreate,
    current_user: User = Depends(get_current_active_moderator_or_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new story. Requires Moderator or Admin role.
    """
    # Ensure the sub_type is set to STORY
    story_in.sub_type = ContentSubType.STORY.value
    
    new_story = await content_crud.create_content(
        db=db, 
        obj_in=story_in, 
        author_id=current_user.id
    )
    return new_story


@router.put("/stories/{story_id}", response_model=ContentResponse, tags=[STORY_TAG])
async def update_existing_story(
    story_id: PyUUID, # Expect UUID
    story_in: ContentUpdate,
    current_user: User = Depends(get_current_user), # More granular check below
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing story.
    Requires Admin, Moderator, or the story author.
    """
    db_story = await content_crud.get_content(db, content_id=story_id, sub_type_str=ContentSubType.STORY.value)
    if not db_story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    # Permission check
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = db_story.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    updated_story = await content_crud.update(db=db, db_obj=db_story, obj_in=story_in)
    return updated_story

@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[STORY_TAG])
async def delete_existing_story(
    story_id: PyUUID, # Expect UUID
    current_user: User = Depends(get_current_active_admin), # Only admins can delete
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a story. Requires Admin role.
    """
    db_story = await content_crud.get_content(db, content_id=story_id, sub_type_str=ContentSubType.STORY.value)
    if not db_story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    
    await content_crud.remove(db=db, id=story_id)
    return # No content response for 204
