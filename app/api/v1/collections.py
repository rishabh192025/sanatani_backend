# app/api/v1/collections.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID as PyUUID

from app.dependencies import get_async_db, get_current_user, get_current_active_admin, get_current_active_moderator_or_admin
from app.schemas.collection import (
    CollectionCreate, CollectionResponse, CollectionUpdate, CollectionResponseWithItems,
    CollectionItemCreate, CollectionItemResponse, CollectionItemUpdate
)
from app.schemas.pagination import PaginatedResponse
from app.crud.collection import collection_crud, collection_item_crud
from app.models.user import User
from app.models.content import Content # For checking content existence

router = APIRouter()
COLLECTION_TAG = "Collections"
ITEM_TAG = "Collection Items" # For sub-resources

@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED, tags=[COLLECTION_TAG])
async def create_new_collection_api(
    collection_in: CollectionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    collection = await collection_crud.create_collection(
        db=db, 
        obj_in=collection_in, 
        #curator_id="1f3d72a7-f5cf-4200-8300-77c13cad6117" # For now, hardcoded curator ID
        curator_id=current_user.id # Assign current user as curator
    )
    print(collection)
    # The CollectionResponse has items: List[CollectionItemResponse] = [], so it will be empty here.
    return collection

@router.get("", response_model=PaginatedResponse[CollectionResponseWithItems], tags=[COLLECTION_TAG])
async def list_all_collections_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_featured: Optional[bool] = Query(None),
    # curator_id: Optional[PyUUID] = Query(None), # If you want to filter by curator
    current_user: User = Depends(get_current_user), # Optional: if you want to filter by user
    db: AsyncSession = Depends(get_async_db),
):
    # For public listing, default is_public=True
    collections, total_count = await collection_crud.get_all_collections_and_count(
        db, skip=skip, limit=limit, is_public=True, is_featured=is_featured , load_items_with_content=True#, curator_id=None
    )
    # These collection responses will have empty items list by default, which is fine for a list view.
    # If you wanted to show item counts, you'd need another query or a hybrid property on Collection.
    response_items = [CollectionResponseWithItems.model_validate(col) for col in collections]
    # ... (pagination next/prev page logic - copy from book.py list endpoint) ...
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

    return PaginatedResponse[CollectionResponseWithItems](
        total_count=total_count, limit=limit, skip=skip, 
        next_page=next_page, prev_page=prev_page, items=response_items
    )

@router.get("/{collection_id_or_slug}", response_model=CollectionResponseWithItems, tags=[COLLECTION_TAG])
async def get_single_collection_api(
    collection_id_or_slug: str,
    current_user: User = Depends(get_current_user), # Optional: if you want to check permissions
    db: AsyncSession = Depends(get_async_db)
):
    collection_model_from_db = None # Renamed for clarity
    try:
        collection_uuid = PyUUID(collection_id_or_slug)
        collection_model_from_db = await collection_crud.get_collection_by_id(
            db, collection_id=collection_uuid, load_items_with_content=True
        )
    except ValueError:
        collection_model_from_db = await collection_crud.get_collection_by_slug(
            db, slug=collection_id_or_slug, load_items_with_content=True
        )
    
    if not collection_model_from_db or not collection_model_from_db.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found or not public")
    
    # Step 1: Validate the main collection model against CollectionResponseWithItems
    # This will populate all fields of CollectionResponseWithItems EXCEPT for the 'items' list initially.
    # Pydantic will use the default `items: List[CollectionItemResponse] = []` from the schema.
    pydantic_collection_response = CollectionResponseWithItems.model_validate(collection_model_from_db)

    # Step 2: Process the items separately if they exist and were loaded
    # The CRUD method `get_collection_by_id` with `load_items_with_content=True`
    # should have loaded `collection_model_from_db.items` and for each item, `item.content`.
    
    processed_items_for_response = []
    if collection_model_from_db.items: # Check if items list is not None and not empty
        for db_item in collection_model_from_db.items:
            # db_item is a SQLAlchemy CollectionItem instance.
            # db_item.content should be a SQLAlchemy Content instance because of joinedload.
            
            # Validate db_item against CollectionItemResponse.
            # This will also validate db_item.content against ContentResponse
            # if CollectionItemResponse.content is typed as ContentResponse.
            pydantic_item = CollectionItemResponse.model_validate(db_item)
            processed_items_for_response.append(pydantic_item)
            
    # Step 3: Assign the processed list of Pydantic items to the collection response
    pydantic_collection_response.items = processed_items_for_response
    
    return pydantic_collection_response


@router.put("/{collection_id}", response_model=CollectionResponseWithItems, tags=[COLLECTION_TAG])
async def update_existing_collection_api(
    collection_id: PyUUID,
    collection_in: CollectionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    db_collection = await collection_crud.get_collection_by_id(db, collection_id=collection_id)
    if not db_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
    # Add ownership/curator check if db_collection.curator_id and current_user.id
    # if db_collection.curator_id and db_collection.curator_id != current_user.id and current_user.role != UserRole.ADMIN.value:
    #      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to update this collection")

    updated_collection_model = await collection_crud.update(db=db, db_obj=db_collection, obj_in=collection_in)
    
    # Return with items loaded
    collection_for_response = await collection_crud.get_collection_by_id(db, collection_id=updated_collection_model.id, load_items_with_content=True)
    if not collection_for_response: # Should not happen
        raise HTTPException(status_code=500, detail="Failed to retrieve updated collection with items.")

    response_items = [CollectionResponseWithItems.model_validate(item) for item in collection_for_response.items or []]
    validated_collection = CollectionResponseWithItems.model_validate(collection_for_response)
    validated_collection.items = response_items
    return validated_collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[COLLECTION_TAG])
async def delete_existing_collection_api(
    collection_id: PyUUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    db_collection = await collection_crud.get_collection_by_id(db, collection_id=collection_id)
    if not db_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
    # Add ownership/curator check
    # if db_collection.curator_id and db_collection.curator_id != current_user.id and current_user.role != UserRole.ADMIN.value:
    #      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this collection")

    await collection_crud.remove(db=db, id=collection_id)
    return

# --- Collection Item Sub-Resource Endpoints ---

@router.post("/{collection_id}/items", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED, tags=[ITEM_TAG])
async def add_item_to_collection_api( # Renamed from endpoint
    collection_id: PyUUID,
    item_in: CollectionItemCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    collection = await collection_crud.get_collection_by_id(db, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Permission check for modifying collection
    # if collection.curator_id and collection.curator_id != current_user.id and current_user.role != UserRole.ADMIN.value:
    #      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to modify this collection's items")

    # Ensure content item exists (optional, FK constraint will catch it)
    from app.crud.content import content_crud # Generic content CRUD
    content_to_add = await content_crud.get_content(db, content_id=item_in.content_id)
    if not content_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item to add not found")

    try:
        new_item_model = await collection_item_crud.add_item_to_collection(
            db, obj_in=item_in, collection_id=collection_id # content_id is in item_in
        )
    except ValueError as e: # Catches "already exists"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # new_item_model already has content loaded due to CRUD method
    return new_item_model # Pydantic will validate against CollectionItemResponse

@router.put("/{collection_id}/items/{item_id}", response_model=CollectionItemResponse, tags=[ITEM_TAG])
async def update_collection_item_api( # Renamed from endpoint
    collection_id: PyUUID,
    item_id: PyUUID,
    item_in: CollectionItemUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    db_item = await collection_item_crud.get_collection_item_by_id(db, item_id=item_id)
    if not db_item or db_item.collection_id != collection_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found in this collection")

    # Permission check (based on parent collection)
    collection = await collection_crud.get_collection_by_id(db, collection_id=collection_id)
    # if collection.curator_id and collection.curator_id != current_user.id and current_user.role != UserRole.ADMIN.value:
    #      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to modify this collection's items")

    updated_item_model = await collection_item_crud.update_collection_item_details(db=db, db_item=db_item, obj_in=item_in)
    return updated_item_model

@router.delete("/{collection_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[ITEM_TAG])
async def remove_item_from_collection_api( # Renamed from endpoint
    collection_id: PyUUID,
    item_id: PyUUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Permission check (based on parent collection)
    collection = await collection_crud.get_collection_by_id(db, collection_id=collection_id)
    if not collection: # Should not happen if item exists within it, but good check
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # if collection.curator_id and collection.curator_id != current_user.id and current_user.role != UserRole.ADMIN.value:
    #      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to modify this collection's items")

    removed_item = await collection_item_crud.remove_item_from_collection(
        db, item_id=item_id # collection_id check is inside CRUD
    )
    if not removed_item or removed_item.collection_id != collection_id: # Extra check
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found or does not belong to this collection")
    return

@router.get("/{collection_id}/items", response_model=PaginatedResponse[CollectionItemResponse], tags=[ITEM_TAG])
async def list_items_in_collection_api(
    request: Request, # For constructing pagination URLs
    collection_id: PyUUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user), # Optional: if collection visibility depends on user
    db: AsyncSession = Depends(get_async_db),
):
    # Check if collection exists and if user has permission to view it
    collection = await collection_crud.get_collection_by_id(db, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # TODO: Add permission check if the collection is private
    # if not collection.is_public and (not current_user or collection.curator_id != current_user.id):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this collection's items")

    items, total_count = await collection_item_crud.get_items_for_collection_paginated(
        db=db,
        collection_id=collection_id,
        skip=skip,
        limit=limit,
        load_content_details=True # Always load for CollectionItemResponse which expects it
    )

    # Construct next and previous page URLs
    next_page, prev_page = None, None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_params["limit"] = str(limit) # Ensure limit is also passed for consistency
        next_page = str(request.url.replace_query_params(**next_params))
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_params["limit"] = str(limit) # Ensure limit is also passed
        prev_page = str(request.url.replace_query_params(**prev_params))
    
    return PaginatedResponse[CollectionItemResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=items # The CRUD method already loads content if specified
    )