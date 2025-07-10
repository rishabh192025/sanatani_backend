# app/api/v1/teachings.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.schemas.teaching import TeachingCreate, TeachingUpdate, TeachingResponse
from app.schemas.pagination import PaginatedResponse
from app.crud.teaching import teaching_crud
from app.models.user import User, UserRole
from app.models.content import ContentStatus, ContentType as ModelContentTypeEnum
from app.dependencies import get_async_db, get_current_user, get_current_active_moderator_or_admin, get_current_active_admin
from uuid import UUID as PyUUID


router = APIRouter()
TEACHING_TAG = "Teachings"

@router.post("", response_model=TeachingResponse, status_code=status.HTTP_201_CREATED, tags=[TEACHING_TAG])
async def create_new_teaching_api(
    teaching_in: TeachingCreate, # Using TeachingCreate
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    # Validate teaching_in.content_type (already done in TeachingCreate if using enum directly)
    # Or add explicit validation here if content_type is string in schema:
    if teaching_in.content_type not in [ModelContentTypeEnum.ARTICLE, ModelContentTypeEnum.AUDIO, ModelContentTypeEnum.VIDEO]:
        raise HTTPException(status_code=400, detail=f"Invalid teaching content_type. Must be ARTICLE, AUDIO, or VIDEO.")
    
    if teaching_in.content_type == ModelContentTypeEnum.ARTICLE and not teaching_in.description:
        raise HTTPException(status_code=400, detail="description is required for ARTICLE content_type teachings.")
    # Add more validation for file_url/duration if content_type is AUDIO/VIDEO if needed

    teaching = await teaching_crud.create_teaching(
        db=db, 
        obj_in=teaching_in,
        #author_id="1f3d72a7-f5cf-4200-8300-77c13cad6117"
        author_id=current_user.id
        )
    return teaching # Pydantic converts Content model to TeachingResponse

@router.get("", response_model=PaginatedResponse[TeachingResponse], tags=[TEACHING_TAG])
async def list_all_teachings_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    content_type: Optional[str] = Query(None, description="Filter by teaching content_type: ARTICLE, AUDIO, VIDEO"),
    status_filter: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user), # Optional: if you want to filter by user permissions
    db: AsyncSession = Depends(get_async_db)
):
    final_status_str = status_filter #if status_filter else ContentStatus.PUBLISHED.value
    teaching_models, total_count = await teaching_crud.get_teachings_list_and_count(
        db, skip=skip, limit=limit, content_type_str=content_type, status_str=final_status_str,
        category_id_str=category_id, language_str=language, search_query=search
    )
    response_items = [TeachingResponse.model_validate(t) for t in teaching_models]
    
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

    return PaginatedResponse[TeachingResponse](
        total_count=total_count, limit=limit, skip=skip, 
        next_page=next_page, prev_page=prev_page, items=response_items
    )

@router.get("/{teaching_id_or_slug}", response_model=TeachingResponse, tags=[TEACHING_TAG])
async def get_single_teaching_api(
    teaching_id_or_slug: str,
    current_user: User = Depends(get_current_user), # Optional: if you want to filter by user permissions
    db: AsyncSession = Depends(get_async_db)
):
    teaching_model = None
    try:
        teaching_uuid = PyUUID(teaching_id_or_slug)
        teaching_model = await teaching_crud.get_teaching(db, teaching_id=teaching_uuid)
    except ValueError:
        teaching_model = await teaching_crud.get_teaching_by_slug(db, slug=teaching_id_or_slug)
    
    if not teaching_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching not found")
    return teaching_model # Pydantic converts

@router.put("/{teaching_id}", response_model=TeachingResponse, tags=[TEACHING_TAG])
async def update_existing_teaching_api(
    teaching_id: PyUUID,
    teaching_in: TeachingUpdate, # Using TeachingUpdate
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    db_teaching = await teaching_crud.get_teaching(db, teaching_id=teaching_id)
    if not db_teaching:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching not found")

    updated_teaching = await teaching_crud.update_teaching(db=db, db_obj=db_teaching, obj_in=teaching_in)
    return updated_teaching # Pydantic converts

@router.delete("/{teaching_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[TEACHING_TAG])
async def delete_existing_teaching_api(
    teaching_id: PyUUID,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    db_teaching = await teaching_crud.get_teaching(db, teaching_id=teaching_id)
    if not db_teaching: # Ensure it's a teaching before deleting
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching not found")
    
    await teaching_crud.remove(db=db, id=teaching_id) # Generic remove
    return