# app/api/v1/book.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Request
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
from app.models.content import BookType as ModelBookTypeEnum # For mapping back in response
from app.models.content import ContentType as ModelContentTypeEnum
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
from app.schemas.pagination import PaginatedResponse

router = APIRouter()

@router.get("", response_model=PaginatedResponse[BookResponse], summary="List all books with pagination")
async def list_all_books_paginated( # Renamed for clarity
    request: Request, # Inject Request to build next/prev page URLs
    skip: int = Query(0, ge=0, description="Number of items to skip (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g., EN, HI)"),
    status_filter: Optional[str] = Query(None, description="Filter by content status (e.g., PUBLISHED, DRAFT)"),
    search: Optional[str] = Query(None, description="Search query for title and description"),
    book_format: Optional[str] = Query(None, description=f"Filter by book format: {', '.join([bt.value for bt in ModelBookTypeEnum])}"), # TEXT, AUDIO, PDF
    db: AsyncSession = Depends(get_async_db)
):
    content_type_filter = None
    if book_format:
        try:
            # Map book_format (TEXT, AUDIO, PDF) to Content.content_type (BOOK, AUDIO, PDF_TYPE_IN_CONTENT_MODEL)
            bf_upper = book_format.upper()
            if bf_upper == ModelBookTypeEnum.AUDIO.value:
                content_type_filter = ModelContentTypeEnum.AUDIO.value
            elif bf_upper == ModelBookTypeEnum.PDF.value:
                # Assuming you have a ContentTypeEnum.PDF or similar
                # If ContentTypeEnum.BOOK is for text/pdf, adjust this logic
                # For this example, let's assume ContentTypeEnum.BOOK handles text/pdf
                content_type_filter = ModelContentTypeEnum.BOOK.value # Or a specific PDF type if you have it
            elif bf_upper == ModelBookTypeEnum.TEXT.value:
                content_type_filter = ModelContentTypeEnum.BOOK.value
            else:
                raise HTTPException(status_code=400, detail="Invalid book_format specified.")
        except KeyError: # Should not happen if bf_upper matches ModelBookTypeEnum values
             raise HTTPException(status_code=400, detail="Invalid book_format specified.")


    books, total_count = await book_crud.get_book_list_and_count(
        db=db, 
        skip=skip, 
        limit=limit,
        content_type_filter_str=content_type_filter, # Pass the determined content_type
        category_id_str=category_id,
        language_str=language,
        status_str=status_filter or ContentStatus.PUBLISHED.value,
        search_query=search
    )

    response_items = []
    for book_model in books:
        derived_book_format = None
        if book_model.content_type == ModelContentTypeEnum.AUDIO.value:
            derived_book_format = ModelBookTypeEnum.AUDIO.value
        elif book_model.content_type == ModelContentTypeEnum.BOOK.value:
            derived_book_format = ModelBookTypeEnum.TEXT.value # Or PDF if that's the case
        else:
            derived_book_format = ModelBookTypeEnum.PDF.value
        book_resp = BookResponse.model_validate(book_model) # Pydantic v2

        book_resp.book_format = derived_book_format
        response_items.append(book_resp)

    # Construct next and previous page URLs
    next_page = None
    if (skip + limit) < total_count:
        # Keep existing query params for the next page URL
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_params["limit"] = str(limit)
        next_page = str(request.url.replace_query_params(**next_params))

    prev_page = None
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_params["limit"] = str(limit)
        prev_page = str(request.url.replace_query_params(**prev_params))
        
    return PaginatedResponse[BookResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )

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


@router.post(
    "/{book_id}/chapters", 
    response_model=BookChapterResponse, 
    status_code=status.HTTP_201_CREATED
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

# Example for GET single chapter:
@router.get(
    "/{book_id}/chapters/{chapter_id}", 
    response_model=BookChapterResponse
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
    response_model=PaginatedResponse[BookChapterResponse],
)
async def list_book_chapters_paginated_route( 
    request: Request,
    book_id: PyUUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    include_sections: bool = Query(False, description="Whether to include sections for each chapter"),
    db: AsyncSession = Depends(get_async_db)
):
    book = await book_crud.get_book(db, content_id=book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    chapters, total_count = await book_chapter_crud.get_chapters_for_book_and_count(
        db=db, book_id=book_id, skip=skip, limit=limit, load_sections=include_sections
    )

    # Construct next and previous page URLs
    next_page = None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_params["limit"] = str(limit)
        next_page = str(request.url.replace_query_params(**next_params))

    prev_page = None
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_params["limit"] = str(limit)
        prev_page = str(request.url.replace_query_params(**prev_params))
        
    return PaginatedResponse[BookChapterResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=chapters # The items themselves
    )

@router.put(
    "/{book_id}/chapters/{chapter_id}",
    response_model=BookChapterResponse
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
    status_code=status.HTTP_204_NO_CONTENT
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


@router.post(
    "/{book_id}/chapters/{chapter_id}/sections", 
    response_model=BookSectionResponse, 
    status_code=status.HTTP_201_CREATED
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

@router.get(
    "/{book_id}/chapters/{chapter_id}/sections/{section_id}", 
    response_model=BookSectionResponse
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
    response_model=PaginatedResponse[BookSectionResponse],
)
async def list_book_sections_paginated_route(
    request: Request,
    book_id: PyUUID,
    chapter_id: PyUUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_async_db)
):
    # Verify chapter exists and belongs to the book
    chapter = await book_chapter_crud.get_chapter_by_id(db=db, chapter_id=chapter_id, book_id=book_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to this book")

    sections, total_count = await book_section_crud.get_sections_for_chapter_and_count(
        db=db, chapter_id=chapter_id, skip=skip, limit=limit
    )

    # Construct next and previous page URLs
    next_page = None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_params["limit"] = str(limit)
        next_page = str(request.url.replace_query_params(**next_params))

    prev_page = None
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_params["limit"] = str(limit)
        prev_page = str(request.url.replace_query_params(**prev_params))
        
    return PaginatedResponse[BookSectionResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=sections
    )


@router.put(
    "/{book_id}/chapters/{chapter_id}/sections/{section_id}",
    response_model=BookSectionResponse
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
    status_code=status.HTTP_204_NO_CONTENT
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
