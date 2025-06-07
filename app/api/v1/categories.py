# app/api/v1/categories.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID as PyUUID

from app.dependencies import get_async_db, get_current_active_admin # Admin for create/update/delete
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.pagination import PaginatedResponse
from app.crud.category import category_crud
from app.models.category import CategoryScopeType, Category # Import model for type hint

router = APIRouter()

CATEGORY_TAG = "Categories"

@router.post(
    "", 
    response_model=CategoryResponse, 
    status_code=status.HTTP_201_CREATED, 
    tags=[CATEGORY_TAG],
    summary="Create a new category"
)
async def create_new_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    #current_admin: User = Depends(get_current_active_admin) # Example: Only admins can create
):
    try:
        category = await category_crud.create_category(db=db, obj_in=category_in)
    except ValueError as e: # Catch errors from CRUD (e.g., slug exists, parent_id invalid)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return category

@router.get(
    "", 
    response_model=List[CategoryResponse], 
    tags=[CATEGORY_TAG],
    summary="List categories by type"
)
async def list_categories_by_type(
    request: Request,
    type: str,
    parent_id: Optional[str] = Query(None, description="Filter by parent category ID to get children. If not provided, lists top-level categories for the type."),
    #skip: int = Query(0, ge=0),
    #limit: int = Query(25, ge=1, le=100),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    #load_children_in_list: bool = Query(False, alias="loadChildren", description="Set to true to load direct children for each category in the list"),
    db: AsyncSession = Depends(get_async_db)
):
    parent_uuid: Optional[PyUUID] = None
    if parent_id:
        try:
            parent_uuid = PyUUID(parent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent_id format.")

    categories, total_count = await category_crud.get_categories_by_type( # Make sure CRUD method uses 'scope' or 'type' consistently
        db=db, 
        type=type, # Pass the enum member directly
        parent_id=parent_uuid,
        skip=skip, 
        limit=limit,
        is_active=is_active,
        #load_children=load_children_in_list # Use the query param
    )
    response_items = []
    for cat_model in categories:

        response_items.append(CategoryResponse.model_validate(cat_model))
    '''
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
        
    return PaginatedResponse[CategoryResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )
    '''
    return response_items
@router.get(
    "/{category_id_or_slug}", 
    response_model=CategoryResponse, 
    tags=[CATEGORY_TAG],
    summary="Get a specific category by ID or slug"
)
async def get_single_category(
    category_id_or_slug: str,
    #load_children: bool = Query(False, description="Whether to load direct children"),
    db: AsyncSession = Depends(get_async_db)
):
    category: Optional[Category] = None
    try:
        cat_uuid = PyUUID(category_id_or_slug)
        category = await category_crud.get(db, id=cat_uuid)
    except ValueError: # Not a UUID, try slug
        # If loading children by slug, get_category_by_slug needs to be adapted or do a two-step fetch
        category = await category_crud.get_category_by_slug(db, slug=category_id_or_slug)

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.put(
    "/{category_id}", 
    response_model=CategoryResponse, 
    tags=[CATEGORY_TAG],
    summary="Update a category"
)
async def update_existing_category(
    category_id: PyUUID,
    category_in: CategoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    #current_admin: User = Depends(get_current_active_admin)
):
    db_category = await category_crud.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        updated_category = await category_crud.update_category(db=db, db_obj=db_category, obj_in=category_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return updated_category

@router.delete(
    "/{category_id}", 
    status_code=status.HTTP_204_NO_CONTENT, 
    tags=[CATEGORY_TAG],
    summary="Delete a category"
)
async def delete_existing_category(
    category_id: PyUUID,
    db: AsyncSession = Depends(get_async_db),
    #current_admin: User = Depends(get_current_active_admin)
):
    db_category = await category_crud.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Consider logic for handling children: disallow delete if children exist, re-parent children, or cascade delete.
    # The model has cascade="all, delete-orphan" on Category.children, so deleting parent deletes children.
    # If children exist and you don't want them deleted, you might check here:
    # if db_category.children: # This requires loading children relationship
    #     raise HTTPException(status_code=400, detail="Cannot delete category with children. Re-parent or delete children first.")

    await category_crud.remove(db=db, id=category_id)
    return