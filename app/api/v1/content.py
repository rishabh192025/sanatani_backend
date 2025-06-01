# app/api/v1/content.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from typing import List, Optional
from uuid import UUID as PyUUID

from app.database import get_async_db # Changed
from app.schemas.content import ContentCreate, ContentResponse, ContentUpdate
from app.crud.content import content_crud
from app.dependencies import get_current_user, get_current_active_moderator_or_admin, get_current_active_admin
from app.models.user import User
from app.models.content import Content # For type hinting
from app.services.file_service import file_service # Placeholder

router = APIRouter()

@router.get("", response_model=List[ContentResponse])
async def get_all_content( # Renamed for clarity
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    content_type: Optional[str] = Query(None, description="Filter by content type (e.g., BOOK, ARTICLE)"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g., EN, HI)"),
    status_filter: Optional[str] = Query(None, description="Filter by content status (e.g., PUBLISHED, DRAFT)"),
    search: Optional[str] = Query(None, description="Search query for title and description"),
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Get a list of content items with optional filters and pagination.
    Publicly accessible for published content.
    """
    # For public listing, you might want to default to only 'PUBLISHED' status
    # or handle it based on user role if drafts are shown to admins.
    # Current implementation of get_content_list allows filtering by status.
    contents = await content_crud.get_content_list(
        db=db, 
        skip=skip, 
        limit=limit,
        content_type_str=content_type,
        category_id_str=category_id,
        language_str=language,
        status_str=status_filter or "PUBLISHED", # Default to published for public view
        search_query=search
    )
    return contents

@router.get("/{content_id_or_slug}", response_model=ContentResponse)
async def get_single_content( # Renamed
    content_id_or_slug: str,
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Get a specific content item by its UUID or slug.
    """
    content: Optional[Content] = None
    try:
        # Try to interpret as UUID first
        content_uuid = PyUUID(content_id_or_slug)
        content = await content_crud.get_content(db=db, content_id=content_uuid)
    except ValueError:
        # If not a valid UUID, assume it's a slug
        content = await content_crud.get_content_by_slug(db=db, slug=content_id_or_slug)
    
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    # Add access control: e.g., only show PUBLISHED content to non-admins/non-authors
    # or if content.status != ContentStatus.PUBLISHED and not (current_user and (current_user.role in [UserRole.ADMIN] or content.author_id == current_user.id)):
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found or not accessible")
    
    return content

@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_content( # Renamed
    content_in: ContentCreate, # Changed parameter name for clarity
    current_user: User = Depends(get_current_active_moderator_or_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Create new content. Requires Moderator or Admin role.
    """
    # author_id will be current_user.id
    # author_name can be set from content_in if it's for a traditional author
    # not on the platform. If current_user is the author, author_name can be derived.
    
    new_content = await content_crud.create_content(
        db=db, 
        obj_in=content_in, 
        author_id=current_user.id
    )
    return new_content

@router.put("/{content_id}", response_model=ContentResponse)
async def update_existing_content( # Renamed
    content_id: PyUUID, # Expect UUID
    content_in: ContentUpdate,
    current_user: User = Depends(get_current_user), # More granular check below
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Update existing content.
    Requires Admin, Moderator, or the content author.
    """
    db_content = await content_crud.get_content(db, content_id=content_id)
    if not db_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    # Permission check
    is_admin_or_moderator = current_user.role in ["admin", "moderator"] # Using strings here for now
    is_author = db_content.author_id == current_user.id
    
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
    updated_content = await content_crud.update(db=db, db_obj=db_content, obj_in=content_in)
    return updated_content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_content( # Renamed
    content_id: PyUUID, # Expect UUID
    current_user: User = Depends(get_current_active_admin), # Only admins can delete
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Delete content. Requires Admin role.
    Consider soft delete vs hard delete. CRUDBase.remove does a hard delete.
    """
    db_content = await content_crud.get_content(db, content_id=content_id)
    if not db_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    await content_crud.remove(db=db, id=content_id)
    return # No content response for 204


@router.post("/{content_id}/upload-file", summary="Upload a primary file for content (e.g., PDF, MP3)")
async def upload_content_main_file( # Renamed for clarity
    content_id: PyUUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user), # Granular check below
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Upload a main file associated with a content item.
    Requires Admin, Moderator, or content author.
    """
    db_content = await content_crud.get_content(db, content_id=content_id)
    if not db_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = db_content.author_id == current_user.id
    
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    # Use file_service to handle the upload
    # This service would save the file, potentially to S3 or local storage,
    # and then update the db_content.file_url and db_content.file_size
    try:
        file_url, file_size = await file_service.upload_content_file(
            db=db, 
            content_obj=db_content, 
            file=file, 
            upload_dir_prefix="content_files"
        )
        # The file_service should commit the changes to db_content
        return {"message": "File uploaded successfully", "file_url": file_url, "file_size": file_size}
    except Exception as e:
        # Log the exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File upload failed: {str(e)}")

# Add similar endpoints for cover_image_url and thumbnail_url if direct upload is desired for them too.