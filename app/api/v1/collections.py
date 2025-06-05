# # app/api/v1/collections.py
# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List, Optional
# from uuid import UUID

# from app.dependencies import get_async_db, get_current_user, get_current_active_admin, get_current_active_moderator_or_admin
# from app.schemas.collection import (
#     CollectionCreate, CollectionResponse, CollectionUpdate,
#     CollectionItemCreate, CollectionItemResponse, CollectionItemUpdate
# )
# from app.crud.collection import collection_crud, collection_item_crud
# from app.models.user import User # For permission checks

# router = APIRouter()

# COLLECTION_TAG = "Collections"

# @router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED, tags=[COLLECTION_TAG])
# async def create_new_collection(
#     collection_in: CollectionCreate,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_active_moderator_or_admin) # Or admin only
# ):
#     collection = await collection_crud.create_collection(db=db, obj_in=collection_in)
#     # New collection will have empty items, which is fine for create
#     return collection

# @router.get("/", response_model=List[CollectionResponse], tags=[COLLECTION_TAG])
# async def get_all_collections(
#     skip: int = Query(0, ge=0),
#     limit: int = Query(10, ge=1, le=100),
#     is_featured: Optional[bool] = Query(None),
#     db: AsyncSession = Depends(get_async_db),
#     # current_user: Optional[User] = Depends(get_current_user_optional) # Optional auth
# ):
#     # Public collections are generally fine, or filter based on current_user if needed
#     collections = await collection_crud.get_all_collections(
#         db, skip=skip, limit=limit, is_public=True, is_featured=is_featured # Default to public
#     )
#     # Note: This doesn't load items for the list view by default for performance.
#     return collections

# @router.get("/{collection_id_or_slug}", response_model=CollectionResponse, tags=[COLLECTION_TAG])
# async def get_single_collection(
#     collection_id_or_slug: str,
#     db: AsyncSession = Depends(get_async_db)
# ):
#     collection = None
#     try:
#         collection_uuid = UUID(collection_id_or_slug)
#         collection = await collection_crud.get_collection(db, id=collection_uuid, load_items=True)
#     except ValueError:
#         collection = await collection_crud.get_collection_by_slug(db, slug=collection_id_or_slug, load_items=True)
    
#     if not collection or not collection.is_public: # Add more access control if needed
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found or not public")
#     return collection

# @router.put("/{collection_id}", response_model=CollectionResponse, tags=[COLLECTION_TAG])
# async def update_existing_collection(
#     collection_id: UUID,
#     collection_in: CollectionUpdate,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_active_moderator_or_admin) # Permission
# ):
#     db_collection = await collection_crud.get_collection(db, id=collection_id)
#     if not db_collection:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
#     # Add ownership/curator check if implemented
    
#     updated_collection = await collection_crud.update(db=db, db_obj=db_collection, obj_in=collection_in)
#     # To return items after update:
#     return await collection_crud.get_collection(db, id=updated_collection.id, load_items=True)


# @router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[COLLECTION_TAG])
# async def delete_existing_collection(
#     collection_id: UUID,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_active_admin) # Stricter permission for delete
# ):
#     db_collection = await collection_crud.get_collection(db, id=collection_id)
#     if not db_collection:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
#     await collection_crud.remove(db=db, id=collection_id) # Cascade should delete items
#     return

# # --- Collection Item Endpoints ---
# ITEM_TAG = "Collection Items"

# @router.post("/{collection_id}/items/", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED, tags=[ITEM_TAG])
# async def add_item_to_collection_endpoint(
#     collection_id: UUID,
#     item_in: CollectionItemCreate, # Contains content_id and sort_order
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_active_moderator_or_admin)
# ):
#     collection = await collection_crud.get_collection(db, id=collection_id)
#     if not collection:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
#     # Ensure content item exists (optional check, FK constraint will catch it too)
#     # from app.crud.content import content_crud
#     # content_item = await content_crud.get_content(db, content_id=item_in.content_id)
#     # if not content_item:
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item to add not found")

#     try:
#         new_item = await collection_item_crud.add_item_to_collection(
#             db, collection_id=collection_id, content_id=item_in.content_id, obj_in=item_in
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     return new_item

# @router.put("/{collection_id}/items/{item_id}", response_model=CollectionItemResponse, tags=[ITEM_TAG])
# async def update_collection_item_endpoint(
#     collection_id: UUID, # For path consistency, not strictly needed if item_id is globally unique
#     item_id: UUID,
#     item_in: CollectionItemUpdate,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_active_moderator_or_admin)
# ):
#     db_item = await collection_item_crud.get_collection_item_by_id(db, item_id=item_id)
#     if not db_item or db_item.collection_id != collection_id:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found in this collection")

#     updated_item = await collection_item_crud.update_collection_item(db, item_id=item_id, obj_in=item_in)
#     return updated_item


# @router.delete("/{collection_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=[ITEM_TAG])
# async def remove_item_from_collection_endpoint(
#     collection_id: UUID, # For path consistency
#     item_id: UUID,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_active_moderator_or_admin)
# ):
#     removed_item = await collection_item_crud.remove_item_from_collection(
#         db, collection_id=collection_id, item_id=item_id
#     )
#     if not removed_item:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found")
#     return