# app/api/v1/book.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID as PyUUID

from app.database import get_async_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.crud.book import book_crud
from app.dependencies import get_current_user, get_current_active_moderator_or_admin, get_current_active_admin
from app.models.user import User
from app.models.content import Content, ContentStatus, ContentType, ContentSubType # For type hinting
from app.services.file_service import file_service

from app.crud.book_chapter import book_chapter_crud # New
from app.crud.book_section import book_section_crud # New
from app.schemas.book_chapter import (
    BookChapterCreate, # Using specific if you keep them separate
    BookChapterResponse,
    BookChapterUpdate
)
from app.schemas.book_section import (
    BookSectionCreate,
    BookSectionResponse,
    BookSectionUpdate
)

router = APIRouter()

@router.get("", response_model=List[BookResponse], summary="List all books")
async def list_all_books( # Renamed for clarity
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g., EN, HI)"),
    status_filter: Optional[str] = Query(None, description="Filter by content status (e.g., PUBLISHED, DRAFT)"),
    search: Optional[str] = Query(None, description="Search query for title and description"),
    #book_type: Optional[str] = Query("TEXT", description="Filter by book type: TEXT, AUDIO"),
    db: AsyncSession = Depends(get_async_db)
):
    # mapped_book_type = None
    # if book_type:
    #     try:
    #         mapped_book_type = BookType[book_type.upper()]
    #     except KeyError:
    #         raise HTTPException(status_code=400, detail="Invalid book_type value")

    contents = await book_crud.get_book_list(
        db=db, 
        skip=skip, 
        limit=limit,
        # book_type_filter=mapped_book_type, # Pass to CRUD
        category_id_str=category_id,
        language_str=language,
        status_str=status_filter or ContentStatus.PUBLISHED.value,
        search_query=search
    )
    return contents

@router.get("/{content_id_or_slug}", response_model=BookResponse)
async def get_single_book( # Renamed
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
        content = await book_crud.get_book(db=db, content_id=content_uuid)
    except ValueError:
        # If not a valid UUID, assume it's a slug
        content = await book_crud.get_book_by_slug(db=db, slug=content_id_or_slug)
    
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    # Add access control: e.g., only show PUBLISHED content to non-admins/non-authors
    # or if content.status != ContentStatus.PUBLISHED and not (current_user and (current_user.role in [UserRole.ADMIN] or content.author_id == current_user.id)):
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found or not accessible")
    
    return content

@router.post("",response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_new_book( # Renamed
    content_in: BookCreate, # Changed parameter name for clarity
    #current_user: User = Depends(get_current_active_moderator_or_admin), # Use specific dependency
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Create new content. Requires Moderator or Admin role.
    """
    # author_id will be current_user.id
    # author_name can be set from content_in if it's for a traditional author
    # not on the platform. If current_user is the author, author_name can be derived.
    
    new_content = await book_crud.create_book(
        db=db, 
        obj_in=content_in,
        #author_id=current_user.id,
        author_id="1f3d72a7-f5cf-4200-8300-77c13cad6117"
    )
    print(new_content)
    return new_content

@router.put("/{content_id}",response_model=BookResponse)
async def update_existing_book( # Renamed
    content_id: PyUUID, # Expect UUID
    content_in: BookUpdate,
    #current_user: User = Depends(get_current_user), # More granular check below
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Update existing content.
    Requires Admin, Moderator, or the content author.
    """
    db_content = await book_crud.get_book(db, content_id=content_id)
    if not db_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    # Permission check
    # is_admin_or_moderator = current_user.role in ["admin", "moderator"] # Using strings here for now
    # is_author = db_content.author_id == current_user.id
    
    # if not (is_admin_or_moderator or is_author):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
    updated_content = await book_crud.update(db=db, db_obj=db_content, obj_in=content_in)
    return updated_content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_book( # Renamed
    content_id: PyUUID, # Expect UUID
    #current_user: User = Depends(get_current_active_admin), # Only admins can delete
    db: AsyncSession = Depends(get_async_db) # Changed
):
    """
    Delete content. Requires Admin role.
    Consider soft delete vs hard delete. CRUDBase.remove does a hard delete.
    """
    db_content = await book_crud.get_book(db, content_id=content_id)
    if not db_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    await book_crud.remove(db=db, id=content_id)
    return # No content response for 204

# --- Book Chapter Endpoints ---
BOOK_CHAPTER_TAG = "Book Chapters"

@router.post(
    "/{book_id}/chapters", 
    response_model=BookChapterResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=[BOOK_CHAPTER_TAG]
)
async def create_chapter_for_book_route( # Renamed to avoid conflict if merged
    book_id: PyUUID,
    chapter_in: BookChapterCreate, # Use specific BookChapterCreate
    #current_user: User = Depends(get_current_user), # Permissions
    db: AsyncSession = Depends(get_async_db)
):
    book = await book_crud.get_book(db, content_id=book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Permission check (e.g., Admin, Moderator, or Author of the book)
    # ... (implement your permission logic)

    try:
        chapter = await book_chapter_crud.create_for_book( # Use book_chapter_crud
            db=db, obj_in=chapter_in, book_id=book_id
        )
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return chapter

# ... other chapter endpoints (GET list, GET single, PUT, DELETE) using book_chapter_crud ...
# Example for GET single chapter:
@router.get(
    "/{book_id}/chapters/{chapter_id}", 
    response_model=BookChapterResponse,
    tags=[BOOK_CHAPTER_TAG]
)
async def get_specific_book_chapter_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    include_sections: bool = Query(True, description="Whether to include sections"),
    db: AsyncSession = Depends(get_async_db)
):
    chapter = await book_chapter_crud.get_chapter_by_id( # Use book_chapter_crud
        db=db, chapter_id=chapter_id, book_id=book_id, load_sections=include_sections
    )
    if not chapter: # get_chapter_by_id already checks book_id match if provided
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found for this book")
    return chapter

@router.get(
    "/{book_id}/chapters", 
    response_model=List[BookChapterResponse],
    tags=[BOOK_CHAPTER_TAG]
)
async def list_book_chapters_route(
    book_id: PyUUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all chapters for a specific book.
    """
    book = await book_crud.get_book(db, content_id=book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    chapters = await book_chapter_crud.get_chapters_for_book(
        db=db, book_id=book_id, skip=skip, limit=limit
    )
    return chapters

@router.put(
    "/{book_id}/chapters/{chapter_id}",
    response_model=BookChapterResponse,
    tags=[BOOK_CHAPTER_TAG]
)
async def update_book_chapter_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    chapter_in: BookChapterUpdate, # Use specific BookChapterUpdate
    #current_user: User = Depends(get_current_user), # Permissions
    db: AsyncSession = Depends(get_async_db)
):
    # Verify chapter exists and belongs to book
    chapter = await book_chapter_crud.get_chapter_by_id(db=db, chapter_id=chapter_id, book_id=book_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to this book")

    # Permission check (e.g., Admin, Moderator, or Author of the parent book)
    # ... (implement your permission logic) ...

    try:
        updated_chapter = await book_chapter_crud.update(
            db=db, db_obj=chapter, obj_in=chapter_in
        )
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return updated_chapter
@router.delete(
    "/{book_id}/chapters/{chapter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[BOOK_CHAPTER_TAG]
)
async def delete_book_chapter_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    #current_user: User = Depends(get_current_active_admin), # Only admins can delete
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a book chapter. Requires Admin role.
    """
    chapter = await book_chapter_crud.get_chapter_by_id(db=db, chapter_id=chapter_id, book_id=book_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to this book")
    
    await book_chapter_crud.remove(db=db, id=chapter_id)
    return # No content response for 204


# --- Book Section Endpoints ---
BOOK_SECTION_TAG = "Book Sections"

@router.post(
    "/{book_id}/chapters/{chapter_id}/sections", 
    response_model=BookSectionResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=[BOOK_SECTION_TAG]
)
async def create_section_for_book_chapter_route(
    book_id: PyUUID, 
    chapter_id: PyUUID,
    section_in: BookSectionCreate, # Use specific BookSectionCreate
    #current_user: User = Depends(get_current_user), # Permissions
    db: AsyncSession = Depends(get_async_db)
):
    # Verify chapter exists and belongs to book
    chapter = await book_chapter_crud.get_chapter_by_id(db=db, chapter_id=chapter_id, book_id=book_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to this book")

    # Permission check (e.g., Admin, Moderator, or Author of the parent book)
    # ... (implement your permission logic) ...

    try:
        section = await book_section_crud.create_for_chapter( # Use book_section_crud
            db=db, obj_in=section_in, chapter_id=chapter_id
        )
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create section: {str(e)}")
    return section
# ... other section endpoints (GET list, GET single, PUT, DELETE) using book_section_crud ...
@router.get(
    "/{book_id}/chapters/{chapter_id}/sections/{section_id}", 
    response_model=BookSectionResponse,
    tags=[BOOK_SECTION_TAG]
)
async def get_specific_book_section_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    section_id: PyUUID,
    db: AsyncSession = Depends(get_async_db)
):
    section = await book_section_crud.get_section_by_id( # Use book_section_crud
        db=db, section_id=section_id, chapter_id=chapter_id
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found for this chapter")
    return section

@router.get(
    "/{book_id}/chapters/{chapter_id}/sections", 
    response_model=List[BookSectionResponse],
    tags=[BOOK_SECTION_TAG]
)
async def list_book_sections_route( # Renamed for clarity
    book_id: PyUUID,
    chapter_id: PyUUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all sections for a specific chapter in a book.
    """
    chapter = await book_chapter_crud.get_chapter_by_id(db=db, chapter_id=chapter_id, book_id=book_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to this book")

    sections = await book_section_crud.get_sections_for_chapter(
        db=db, chapter_id=chapter_id, skip=skip, limit=limit
    )
    return sections


@router.put(
    "/{book_id}/chapters/{chapter_id}/sections/{section_id}",
    response_model=BookSectionResponse,
    tags=[BOOK_SECTION_TAG]
)
async def update_book_section_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    section_id: PyUUID,
    section_in: BookSectionUpdate, # Use specific BookSectionUpdate
    #current_user: User = Depends(get_current_user), # Permissions
    db: AsyncSession = Depends(get_async_db)
):
    # Verify section exists and belongs to chapter
    section = await book_section_crud.get_section_by_id(db=db, section_id=section_id, chapter_id=chapter_id)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found or does not belong to this chapter")

    # Permission check (e.g., Admin, Moderator, or Author of the parent book)
    # ... (implement your permission logic) ...

    try:
        updated_section = await book_section_crud.update(
            db=db, db_obj=section, obj_in=section_in
        )
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not update section: {str(e)}")
    return updated_section

@router.delete(
    "/{book_id}/chapters/{chapter_id}/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[BOOK_SECTION_TAG]
)
async def delete_book_section_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    section_id: PyUUID,
    #current_user: User = Depends(get_current_active_admin), # Only admins can delete
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a book section. Requires Admin role.
    """
    section = await book_section_crud.get_section_by_id(db=db, section_id=section_id, chapter_id=chapter_id)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found or does not belong to this chapter")
    
    await book_section_crud.remove(db=db, id=section_id)
    return




'''
@router.post("/{content_id}/upload-file", summary="Upload a primary file for content (e.g., PDF, MP3)")
async def upload_content_main_file( # Renamed for clarity
    content_id: PyUUID,
    file: UploadFile = File(...),
    #current_user: User = Depends(get_current_user), # Granular check below
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

# --- File Upload Endpoint for Content (main file, not chapter specific audio/video) ---
@router.post("/{content_id}/upload-main-file", summary="Upload a primary file for content (e.g., PDF, MP3 for whole book/album)")
async def upload_content_main_file(
    content_id: PyUUID,
    file: UploadFile = File(...),
    #current_user: User = Depends(get_current_user),
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

'''