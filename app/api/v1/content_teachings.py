# from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List, Optional
# from uuid import UUID as PyUUID

# from app.database import get_async_db
# from app.schemas.content import ContentCreate, ContentResponse, ContentUpdate
# from app.schemas.content_chapter import ( # Import chapter schemas
#     ContentChapterCreate, ContentChapterResponse, ContentChapterUpdate
# )
# from app.schemas.content_section import ( # Import section schemas
#     ContentSectionCreate, ContentSectionResponse, ContentSectionUpdate
# )
# from app.crud.content_section import content_section_crud # Import section CRUD
# from app.crud.content import content_crud
# from app.crud.content_chapter import content_chapter_crud # Import chapter CRUD
# from app.dependencies import get_current_user, get_current_active_moderator_or_admin, get_current_active_admin
# from app.models.user import User
# from app.models.content import Content, ContentStatus, ContentType, ContentSubType # For type hinting
# from app.services.file_service import file_service

# router = APIRouter()

# # --- Specific Endpoints for Teachings ---
# TEACHING_TAG = "Teachings"

# @router.get("/teachings/", response_model=List[ContentResponse], tags=[TEACHING_TAG])
# async def get_all_teachings(
#     skip: int = Query(0, ge=0),
#     limit: int = Query(10, ge=1, le=100),
#     teaching_format: Optional[str] = Query(None, description="Filter teachings by format: ARTICLE, AUDIO_CONTENT, VIDEO"),
#     # Add other relevant filters
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """
#     Get a list of content items specifically marked as Teachings.
#     Optionally filter by the teaching_format (which maps to content_type).
#     """
#     # Map teaching_format to content_type if provided
#     content_type_filter = None
#     if teaching_format:
#         try:
#             content_type_filter = ContentType[teaching_format.upper()].value
#         except KeyError:
#             raise HTTPException(status_code=400, detail="Invalid teaching_format specified.")

#     teachings = await content_crud.get_content_list(
#         db=db,
#         skip=skip,
#         limit=limit,
#         sub_type_str=ContentSubType.TEACHING.value, # Filter by sub_type
#         content_type_str=content_type_filter, # Filter by content_type if teaching_format is given
#         status_str=ContentStatus.PUBLISHED.value # Default to published
#     )
#     return teachings

# @router.get("/teachings/{teaching_id_or_slug}", response_model=ContentResponse, tags=[TEACHING_TAG])
# async def get_single_teaching(
#     teaching_id_or_slug: str,
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """
#     Get a specific teaching by its UUID or slug.
#     """
#     teaching: Optional[Content] = None
#     try:
#         # Try to interpret as UUID first
#         teaching_uuid = PyUUID(teaching_id_or_slug)
#         teaching = await content_crud.get_content(db=db, content_id=teaching_uuid, sub_type_str=ContentSubType.TEACHING.value)
#     except ValueError:
#         # If not a valid UUID, assume it's a slug
#         teaching = await content_crud.get_content_by_slug(db=db, slug=teaching_id_or_slug, sub_type_str=ContentSubType.TEACHING.value)
#     if not teaching:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching not found")
#     return teaching

# @router.post("/teachings/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED, tags=[TEACHING_TAG])
# async def create_new_teaching(
#     teaching_in: ContentCreate,
#     current_user: User = Depends(get_current_active_moderator_or_admin), # Use specific dependency
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """
#     Create a new teaching. Requires Moderator or Admin role.
#     """
#     # Ensure the sub_type is set to TEACHING
#     teaching_in.sub_type = ContentSubType.TEACHING.value
    
#     new_teaching = await content_crud.create_content(
#         db=db, 
#         obj_in=teaching_in, 
#         author_id=current_user.id
#     )
#     return new_teaching

# @router.put("/teachings/{teaching_id}", response_model=ContentResponse, tags=[TEACHING_TAG])
# async def update_existing_teaching(
#     teaching_id: PyUUID, # Expect UUID
#     teaching_in: ContentUpdate,
#     #current_user: User = Depends(get_current_user), # More granular check below
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """
#     Update an existing teaching.
#     Requires Admin, Moderator, or the teaching author.
#     """
#     db_teaching = await content_crud.get_content(db, content_id=teaching_id, sub_type_str=ContentSubType.TEACHING.value)
#     if not db_teaching:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching not found")
    
#     # Permission check
#     is_admin_or_moderator = current_user.role in ["admin", "moderator"]
#     is_author = db_teaching.author_id == current_user.id
#     if not (is_admin_or_moderator or is_author):
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
#     updated_teaching = await content_crud.update(db=db, db_obj=db_teaching, obj_in=teaching_in)
#     return updated_teaching

# @router.delete("/teachings/{teaching_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[TEACHING_TAG])
# async def delete_existing_teaching(
#     teaching_id: PyUUID, # Expect UUID
#     current_user: User = Depends(get_current_active_admin), # Only admins can delete
#     db: AsyncSession = Depends(get_async_db)
# ):
#     """
#     Delete a teaching. Requires Admin role.
#     """
#     db_teaching = await content_crud.get_content(db, content_id=teaching_id, sub_type_str=ContentSubType.TEACHING.value)
#     if not db_teaching:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching not found")
    
#     await content_crud.remove(db=db, id=teaching_id)
#     return