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

@router.get("", response_model=List[ContentResponse], summary="List all content (generic)")
async def list_all_generic_content( # Renamed for clarity
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    content_type: Optional[str] = Query(None, description="Filter by content type (e.g., BOOK, ARTICLE)"),
    sub_type: Optional[str] = Query(None, description="Filter by sub-type (e.g., STORY, TEACHING)"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g., EN, HI)"),
    status_filter: Optional[str] = Query(None, description="Filter by content status (e.g., PUBLISHED, DRAFT)"),
    search: Optional[str] = Query(None, description="Search query for title and description"),
    db: AsyncSession = Depends(get_async_db)
):
    contents = await content_crud.get_content_list(
        db=db, 
        skip=skip, 
        limit=limit,
        content_type_str=content_type, # Pass the value
        sub_type_str=sub_type,         # Pass the value
        category_id_str=category_id,   # Pass the value
        language_str=language,       # Pass the value
        status_str=status_filter or ContentStatus.PUBLISHED.value, # Pass the value
        search_query=search            # Pass the value
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

@router.post("/{content_id}/chapters/", response_model=ContentChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter_for_content(
    content_id: PyUUID,
    chapter_in: ContentChapterCreate,
    current_user: User = Depends(get_current_user), # Granular check
    db: AsyncSession = Depends(get_async_db)
):
    content_item = await content_crud.get_content(db, content_id=content_id)
    if not content_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent content not found")

    # Permission check: Admin, Moderator, or Author of the parent content
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = content_item.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to add chapters to this content")

    try:
        chapter = await content_chapter_crud.create_with_content_id(
            db=db, obj_in=chapter_in, content_id=content_id
        )
    except ValueError as e: # Catch duplicate chapter number error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return chapter

@router.get("/{content_id}/chapters/", response_model=List[ContentChapterResponse])
async def list_chapters_for_content(
    content_id: PyUUID,
    include_sections: bool = Query(False, description="Whether to include sections for each chapter in the list"), # Default to false for list view
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_async_db)
):
    content_item = await content_crud.get_content(db, content_id=content_id)
    if not content_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent content not found")
    
    if include_sections:
        chapters = await content_chapter_crud.get_chapters_by_content_id_with_sections(
            db=db, content_id=content_id, skip=skip, limit=limit
        )
    else:
        chapters = await content_chapter_crud.get_chapters_by_content_id(
            db=db, content_id=content_id, skip=skip, limit=limit
        )
    return chapters

@router.get("/{content_id}/chapters/{chapter_id}", response_model=ContentChapterResponse)
async def get_specific_chapter(
    content_id: PyUUID,
    chapter_id: PyUUID,
    include_sections: bool = Query(True, description="Whether to include sections in the response"),
    db: AsyncSession = Depends(get_async_db)
):
    if include_sections:
        chapter = await content_chapter_crud.get_chapter_with_sections(db=db, chapter_id=chapter_id)
    else:
        chapter = await content_chapter_crud.get_chapter(db=db, chapter_id=chapter_id)
        
    if not chapter or chapter.content_id != content_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to specified content")
    return chapter

@router.put("/{content_id}/chapters/{chapter_id}", response_model=ContentChapterResponse)
async def update_specific_chapter(
    content_id: PyUUID,
    chapter_id: PyUUID,
    chapter_in: ContentChapterUpdate,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_async_db)
):
    db_chapter = await content_chapter_crud.get_chapter(db=db, chapter_id=chapter_id) # Fetch without sections first
    if not db_chapter or db_chapter.content_id != content_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    content_item = await content_crud.get_content(db, content_id=db_chapter.content_id) # Get parent
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = content_item and content_item.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this chapter")

    # Check for chapter number change and potential collision
    if chapter_in.chapter_number is not None and chapter_in.chapter_number != db_chapter.chapter_number:
        existing_chapter_with_new_number = await content_chapter_crud.get_by_content_and_chapter_number(
            db, content_id=content_id, chapter_number=chapter_in.chapter_number
        )
        if existing_chapter_with_new_number and existing_chapter_with_new_number.id != chapter_id: # Ensure it's not the same chapter
            raise HTTPException(status_code=400, detail=f"Chapter number {chapter_in.chapter_number} already exists for this content.")

    await content_chapter_crud.update(db=db, db_obj=db_chapter, obj_in=chapter_in) # Perform the update

    # Now, fetch the fully updated chapter with its sections for the response
    updated_chapter_with_sections = await content_chapter_crud.get_chapter_with_sections(db=db, chapter_id=chapter_id)
    if not updated_chapter_with_sections: # Should not happen if update was successful
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Updated chapter could not be retrieved")
    return updated_chapter_with_sections

@router.delete("/{content_id}/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specific_chapter(
    content_id: PyUUID,
    chapter_id: PyUUID,
    current_user: User = Depends(get_current_user), # Granular check
    db: AsyncSession = Depends(get_async_db)
):
    db_chapter = await content_chapter_crud.get_chapter(db=db, chapter_id=chapter_id)
    if not db_chapter or db_chapter.content_id != content_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    content_item = await content_crud.get_content(db, content_id=db_chapter.content_id) # Get parent
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = content_item and content_item.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this chapter")
    
    await content_chapter_crud.remove(db=db, id=chapter_id)
    return

# --- File Upload Endpoint for Content (main file, not chapter specific audio/video) ---
@router.post("/{content_id}/upload-main-file", summary="Upload a primary file for content (e.g., PDF, MP3 for whole book/album)")
async def upload_content_main_file(
    content_id: PyUUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    db_content = await content_crud.get_content(db, content_id=content_id)
    if not db_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = db_content.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    try:
        # This updates content_obj.file_url and file_size
        file_url, file_size = await file_service.upload_content_file(
            db=db, content_obj=db_content, file=file, upload_dir_prefix="content_main_files"
        )
        return {"message": "Main content file uploaded successfully", "file_url": file_url, "file_size_bytes": file_size}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File upload failed: {str(e)}")

# You would need similar upload endpoints for chapter-specific audio/video if ContentChapter.audio_url etc.
# are to be populated via direct uploads rather than just string URLs.
# E.g., POST /{content_id}/chapters/{chapter_id}/upload-audio


@router.post(
    "/{content_id}/chapters/{chapter_id}/sections/", 
    response_model=ContentSectionResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_section_for_chapter(
    content_id: PyUUID, # For verification
    chapter_id: PyUUID,
    section_in: ContentSectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    # Verify chapter exists and belongs to content
    chapter = await content_chapter_crud.get_chapter(db=db, chapter_id=chapter_id)
    if not chapter or chapter.content_id != content_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to specified content")

    # Permission check (similar to creating chapters)
    parent_content = await content_crud.get_content(db, content_id=chapter.content_id)
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = parent_content and parent_content.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to add sections to this chapter")

    try:
        section = await content_section_crud.create_with_chapter_id(
            db=db, obj_in=section_in, chapter_id=chapter_id
        )
    except Exception as e: # Catch potential UniqueConstraint for section_order
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create section: {e}")
    return section

@router.get(
    "/{content_id}/chapters/{chapter_id}/sections/", 
    response_model=List[ContentSectionResponse]
)
async def list_sections_for_chapter(
    content_id: PyUUID, # For verification
    chapter_id: PyUUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_async_db)
):
    chapter = await content_chapter_crud.get_chapter(db=db, chapter_id=chapter_id)
    if not chapter or chapter.content_id != content_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to specified content")

    sections = await content_section_crud.get_sections_by_chapter_id(
        db=db, chapter_id=chapter_id, skip=skip, limit=limit
    )
    return sections

@router.get(
    "/{content_id}/chapters/{chapter_id}/sections/{section_id}", 
    response_model=ContentSectionResponse
)
async def get_specific_section(
    content_id: PyUUID, # For verification
    chapter_id: PyUUID, # For verification
    section_id: PyUUID,
    db: AsyncSession = Depends(get_async_db)
):
    section = await content_section_crud.get_section(db=db, section_id=section_id)
    if not section or section.chapter_id != chapter_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found or does not belong to specified chapter")
    
    # Verify chapter belongs to content (optional, good for consistency)
    # chapter = await content_chapter_crud.get_chapter(db=db, chapter_id=section.chapter_id)
    # if not chapter or chapter.content_id != content_id:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent chapter/content mismatch")
        
    return section

@router.put(
    "/{content_id}/chapters/{chapter_id}/sections/{section_id}", 
    response_model=ContentSectionResponse
)
async def update_specific_section(
    content_id: PyUUID, # For verification
    chapter_id: PyUUID, # For verification
    section_id: PyUUID,
    section_in: ContentSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    db_section = await content_section_crud.get_section(db=db, section_id=section_id)
    if not db_section or db_section.chapter_id != chapter_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found or does not belong to specified chapter")

    # Permission check (similar to updating chapters)
    parent_content = await content_crud.get_content(db, content_id=content_id) # Assuming chapter.content_id can be trusted
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = parent_content and parent_content.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this section")
    
    # Handle potential section_order change and collision
    if section_in.section_order is not None and section_in.section_order != db_section.section_order:
        existing_section_order = await content_section_crud.get_by_chapter_and_order(
            db, chapter_id=chapter_id, section_order=section_in.section_order
        )
        if existing_section_order and existing_section_order.id != section_id : # if it's another section
            raise HTTPException(status_code=400, detail=f"Section order {section_in.section_order} already exists in this chapter.")


    updated_section = await content_section_crud.update(db=db, db_obj=db_section, obj_in=section_in)
    return updated_section

@router.delete(
    "/{content_id}/chapters/{chapter_id}/sections/{section_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_specific_section(
    content_id: PyUUID, # For verification
    chapter_id: PyUUID, # For verification
    section_id: PyUUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    db_section = await content_section_crud.get_section(db=db, section_id=section_id)
    if not db_section or db_section.chapter_id != chapter_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found or does not belong to specified chapter")

    # Permission check (similar to deleting chapters)
    parent_content = await content_crud.get_content(db, content_id=content_id)
    is_admin_or_moderator = current_user.role in ["admin", "moderator"]
    is_author = parent_content and parent_content.author_id == current_user.id
    if not (is_admin_or_moderator or is_author):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this section")
    
    await content_section_crud.remove(db=db, id=section_id)
    return