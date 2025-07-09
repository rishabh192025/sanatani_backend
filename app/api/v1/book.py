# app/api/v1/book.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any
from uuid import UUID as PyUUID

from app.database import get_async_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.crud.book import book_crud
from app.dependencies import get_current_user, get_current_active_moderator_or_admin, get_current_active_admin
from app.models.user import User
from app.models.content import Content, ContentStatus, ContentType, ContentSubType
from app.models.content import BookType as ModelBookTypeEnum
from app.models.content import ContentType as ModelContentTypeEnum
from app.crud.book_chapter import book_chapter_crud
from app.crud.book_section import book_section_crud 
from app.schemas.book_chapter import (
    BookChapterCreate,
    BookChapterResponse,
    BookChapterUpdate, BookChapterResponseWithoutSections

)
from app.schemas.book_section import (
    BookSectionCreate,
    BookSectionResponse,
    BookSectionUpdate
)
from app.schemas.book_toc import (
    BookTableOfContentsResponse,
    TOCChapterItem,
    TOCSectionItem
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter()

@router.get("", response_model=PaginatedResponse[BookResponse], summary="List all books with pagination")
async def list_all_books_paginated(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of items to skip (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g., EN, HI)"),
    status_filter: Optional[str] = Query(None, description="Filter by content status (e.g., PUBLISHED, DRAFT)"),
    search: Optional[str] = Query(None, description="Search query for title and description"),
    book_format: Optional[str] = Query("TEXT", description=f"Filter by book format: {', '.join([bt.value for bt in ModelBookTypeEnum])}"), # TEXT, AUDIO, PDF
    current_user: User = Depends(get_current_user),
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
                content_type_filter = ModelContentTypeEnum.PDF.value # Or a specific PDF type if you have it
            elif bf_upper == ModelBookTypeEnum.TEXT.value:
                content_type_filter = ModelContentTypeEnum.BOOK.value
            elif bf_upper == ModelBookTypeEnum.VIDEO.value:
                content_type_filter = ModelContentTypeEnum.VIDEO.value
            else:
                raise HTTPException(status_code=400, detail="Invalid book_format specified.")
        except KeyError: # Should not happen if bf_upper matches ModelBookTypeEnum values
             raise HTTPException(status_code=400, detail="Invalid book_format specified.")


    books, total_count = await book_crud.get_book_list_and_count(
        db=db, 
        skip=skip, 
        limit=limit,
        content_type_filter_str=content_type_filter,
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
async def get_single_book(
    content_id_or_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
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

    derived_book_format = None
    if content.content_type == ModelContentTypeEnum.AUDIO.value:
        derived_book_format = ModelBookTypeEnum.AUDIO.value
    elif content.content_type == ModelContentTypeEnum.BOOK.value:
        derived_book_format = ModelBookTypeEnum.TEXT.value # Or PDF if that's the case
    elif content.content_type == ModelContentTypeEnum.VIDEO.value:
        derived_book_format = ModelBookTypeEnum.VIDEO.value
    else:
        derived_book_format = ModelBookTypeEnum.PDF.value
    book_resp = BookResponse.model_validate(content) # Pydantic v2

    book_resp.book_format = derived_book_format

    return book_resp


@router.post("",response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_new_book(
    content_in: BookCreate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create new content. Requires Moderator or Admin role.
    """
    # author_id will be current_user.id
    # author_name can be set from content_in if it's for a traditional author
    # not on the platform. If current_user is the author, author_name can be derived.
    print(content_in)
    new_content = await book_crud.create_book(
        db=db, 
        obj_in=content_in,
        author_id=current_user.id,
    )
    print(new_content)
    return new_content

@router.put("/{content_id}",response_model=BookResponse)
async def update_existing_book(
    content_id: PyUUID,
    content_in: BookUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
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
async def delete_existing_book(
    content_id: PyUUID,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
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
    response_model=BookChapterResponseWithoutSections, 
    status_code=status.HTTP_201_CREATED
)
async def create_chapter_for_book_route(
    book_id: PyUUID,
    chapter_in: BookChapterCreate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    book = await book_crud.get_book(db, content_id=book_id) # get_book from CRUDBook
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Permission Check
    # ... (your permission logic based on current_user and book.author_id) ...

    # === LOGIC BASED ON BOOKTYPE (CONTENT_TYPE) ===
    # book.content_type will be 'BOOK' (for text), 'AUDIO', 'PDF', 'VIDEO' based on creation
    book_actual_content_type = ModelContentTypeEnum(book.content_type) # Convert string from DB to enum

    if book_actual_content_type == ModelContentTypeEnum.PDF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapters cannot be added to PDF-type books. The PDF is a single file."
        )
    
    # For AUDIO or VIDEO books, chapter_in might need to contain audio_url/video_url
    # You might want to add validation here or in Pydantic schema for BookChapterCreate
    # e.g., if book.content_type == AUDIO and not chapter_in.audio_url: raise Error

    try:
        chapter_model = await book_chapter_crud.create_for_book(
            db=db, obj_in=chapter_in, book_id=book_id
        )
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return BookChapterResponseWithoutSections.model_validate(chapter_model)

# Example for GET single chapter:
@router.get(
    "/{book_id}/chapters/{chapter_id}"
)
async def get_specific_book_chapter_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    include_sections: bool = Query(True, description="Whether to include sections"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    chapter = await book_chapter_crud.get_chapter_by_id(
        db=db, chapter_id=chapter_id, book_id=book_id, load_sections=include_sections
    )
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found for this book")
    if include_sections:

        return  BookChapterResponse.model_validate(chapter) 
    else:
        return BookChapterResponseWithoutSections.model_validate(chapter) 

@router.get(
    "/{book_id}/chapters", 
    response_model=PaginatedResponse[Any],
)
async def list_book_chapters_paginated_route( 
    request: Request,
    book_id: PyUUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_sections: bool = Query(False, description="Whether to include sections (only applicable for TEXT books)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    book = await book_crud.get_book(db, content_id=book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    book_actual_content_type = ModelContentTypeEnum(book.content_type)

    if book_actual_content_type == ModelContentTypeEnum.PDF:
        # Return empty paginated response or 400
        return PaginatedResponse[BookChapterResponseWithoutSections]( # Or just Any
            total_count=0, limit=limit, skip=skip, items=[] 
        )
        # Alternatively:
        # raise HTTPException(status_code=400, detail="PDF books do not have a chapter list.")

    # Determine if sections should actually be loaded based on book type
    should_load_sections_for_crud = include_sections and (book_actual_content_type == ModelContentTypeEnum.BOOK)

    chapter_models, total_count = await book_chapter_crud.get_chapters_for_book_and_count(
        db=db, book_id=book_id, skip=skip, limit=limit, load_sections=should_load_sections_for_crud
    )
    
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

    processed_items = []
    if should_load_sections_for_crud: 
        for chapter_model in chapter_models:
            processed_items.append(BookChapterResponse.model_validate(chapter_model))
        return PaginatedResponse[BookChapterResponse](
            total_count=total_count, limit=limit, skip=skip, 
            next_page=next_page, prev_page=prev_page, items=processed_items
        )
    else:
        for chapter_model in chapter_models:
            processed_items.append(BookChapterResponseWithoutSections.model_validate(chapter_model))
        return PaginatedResponse[BookChapterResponseWithoutSections](
            total_count=total_count, limit=limit, skip=skip,
            next_page=next_page, prev_page=prev_page, items=processed_items
        )

@router.put(
    "/{book_id}/chapters/{chapter_id}",
    response_model=BookChapterResponseWithoutSections,
)
async def update_book_chapter_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    chapter_in: BookChapterUpdate,
    current_user: User = Depends(get_current_active_admin),
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
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a book chapter. Requires Admin role.
    """
    chapter = await book_chapter_crud.get_chapter_by_id(db=db, chapter_id=chapter_id, book_id=book_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found or does not belong to this book")
    
    await book_chapter_crud.remove(db=db, id=chapter_id)
    return

@router.post(
    "/{book_id}/chapters/{chapter_id}/sections", 
    response_model=BookSectionResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_section_for_book_chapter_route(
    book_id: PyUUID, 
    chapter_id: PyUUID,
    section_in: BookSectionCreate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    # Fetch book to check its content_type
    book = await book_crud.get_book(db, content_id=book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    book_actual_content_type = ModelContentTypeEnum(book.content_type)
    if book_actual_content_type != ModelContentTypeEnum.BOOK: # Only TEXT books (ContentType.BOOK) have sections
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sections are not applicable for this book type ('{book.content_type}'). Only for TEXT books."
        )
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    section = await book_section_crud.get_section_by_id(
        db=db, section_id=section_id, chapter_id=chapter_id
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found for this chapter")
    return section

@router.get(
    "/{book_id}/chapters/{chapter_id}/sections", 
    response_model=PaginatedResponse[BookSectionResponse]
)
async def list_book_sections_paginated_route(
    request: Request,
    book_id: PyUUID,
    chapter_id: PyUUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    # Fetch book to check its content_type
    book = await book_crud.get_book(db, content_id=book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    book_actual_content_type = ModelContentTypeEnum(book.content_type)
    if book_actual_content_type != ModelContentTypeEnum.BOOK: # Only TEXT books (ContentType.BOOK) have sections
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sections are not applicable for this book type ('{book.content_type}'). Only for TEXT books."
        )

    sections, total_count = await book_section_crud.get_sections_for_chapter_and_count(
        db=db, chapter_id=chapter_id, skip=skip, limit=limit
    )
    print(sections, total_count)
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
        total_count=total_count, limit=limit, skip=skip,
        next_page=next_page, prev_page=prev_page, items=sections
    )

@router.put(
    "/{book_id}/chapters/{chapter_id}/sections/{section_id}",
    response_model=BookSectionResponse
)
async def update_book_section_route(
    book_id: PyUUID,
    chapter_id: PyUUID,
    section_id: PyUUID,
    section_in: BookSectionUpdate,
    current_user: User = Depends(get_current_active_admin),
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
    current_user: User = Depends(get_current_active_admin),
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

@router.get(
    "/{book_id_or_slug}/toc",
    response_model=BookTableOfContentsResponse
)
async def get_book_table_of_contents_route(
    book_id_or_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get the table of contents for a book.
    For AUDIO books, it includes audio_url for each chapter.
    For TEXT books, it includes nested sections for each chapter.
    """
    # --- MODIFICATION: Fetch by slug or ID ---
    book_with_structure: Optional[Content] = None
    try:
        book_uuid = PyUUID(book_id_or_slug)
        book_with_structure = await book_crud.get_book_table_of_contents(db=db, book_id=book_uuid)
    except ValueError:
        # Assuming you add a get_by_slug_with_chapters to your CRUD
        # For now, let's assume get_book_table_of_contents can handle this, or you add a new method
        # Let's mock a new CRUD method for clarity:
        book_with_structure = await book_crud.get_book_toc_by_slug(db=db, slug=book_id_or_slug)


    if not book_with_structure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # --- CORE LOGIC MODIFICATION ---
    # Determine the book's format to build the correct response
    book_format = ModelContentTypeEnum(book_with_structure.content_type)
    
    toc_chapters = []
    if book_with_structure.chapters:
        for chapter_model in sorted(book_with_structure.chapters, key=lambda c: c.chapter_number):
            
            # Initialize chapter data
            chapter_data = {
                "id": chapter_model.id,
                "title": chapter_model.title,
                "chapter_number": chapter_model.chapter_number
            }

            # Populate format-specific data
            if book_format == ModelContentTypeEnum.AUDIO:
                # For audio books, add the audio_url
                chapter_data["audio_url"] = chapter_model.audio_url
                chapter_data["sections"] = [] # Audiobooks don't have text sections in this model
            
            elif book_format == ModelContentTypeEnum.BOOK: # This is your 'TEXT' book
                # For text books, populate the sections
                toc_sections = []
                if chapter_model.sections:
                    for section_model in sorted(chapter_model.sections, key=lambda s: s.section_order):
                        toc_sections.append(
                            TOCSectionItem.model_validate(section_model)
                        )
                chapter_data["sections"] = toc_sections

            # Create the Pydantic model from the constructed dictionary
            toc_chapters.append(TOCChapterItem(**chapter_data))
            
    # Construct the final response, now including the cover_image_url
    return BookTableOfContentsResponse(
        book_id=book_with_structure.id,
        book_title=book_with_structure.title,
        cover_image_url=book_with_structure.cover_image_url, # Add the cover image
        chapters=toc_chapters
    )