# app/crud/collection.py
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload # joinedload for content within item
from sqlalchemy import and_, func

from app.crud.base import CRUDBase
from app.models.collection import Collection, CollectionItem
from app.schemas.collection import CollectionCreate, CollectionUpdate, CollectionItemCreate, CollectionItemUpdate
from app.utils.helpers import generate_slug

class CRUDCollection(CRUDBase[Collection, CollectionCreate, CollectionUpdate]):
    async def create_collection(
        self, db: AsyncSession, *, obj_in: CollectionCreate, curator_id: Optional[UUID] = None
    ) -> Collection:
        slug = await generate_slug(db, self.model, obj_in.name)
        collection_data = obj_in.model_dump()
        
        db_obj = Collection(
            **collection_data, 
            slug=slug, 
            #curator_id=curator_id
            )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # For create response, db_obj.items will be empty, which is fine
        return db_obj

    async def get_collection_by_slug(
        self, db: AsyncSession, slug: str, load_items_with_content: bool = False
    ) -> Optional[Collection]:
        query = select(self.model).filter(self.model.slug == slug)
        if load_items_with_content:
            query = query.options(
                selectinload(self.model.items).options( # Load items
                    joinedload(CollectionItem.content)   # Then, for each item, joinload its content
                ) 
            )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_collection_by_id( # Renamed from get_collection for clarity
        self, db: AsyncSession, collection_id: UUID, load_items_with_content: bool = False
    ) -> Optional[Collection]:
        query = select(self.model).filter(self.model.id == collection_id)
        if load_items_with_content:
            query = query.options(
                selectinload(self.model.items).options(
                    joinedload(CollectionItem.content)
                )
            )
        result = await db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_all_collections_and_count( # For pagination
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, 
        is_public: Optional[bool] = None, 
        is_featured: Optional[bool] = None,
        load_items_with_content: bool = False
        #curator_id: Optional[UUID] = None
    ) -> Tuple[List[Collection], int]:
        
        filters = []
        if is_public is not None:
            filters.append(self.model.is_public == is_public)
        if is_featured is not None:
            filters.append(self.model.is_featured == is_featured)
        # if curator_id is not None:
        #     filters.append(self.model.curator_id == curator_id)

        count_query = select(func.count(self.model.id)).select_from(self.model)
        data_query = select(self.model)

        if filters:
            count_query = count_query.where(*filters)
            data_query = data_query.where(*filters)
        
        if load_items_with_content:
            data_query = data_query.options(
                selectinload(self.model.items).options(
                    joinedload(CollectionItem.content)
                )
            )
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        data_query = data_query.order_by(self.model.sort_order, self.model.name).offset(skip).limit(limit)
        # Note: Not loading items by default for list view for performance.
        # If items are needed, add an option and selectinload.
        items_result = await db.execute(data_query)
        items = items_result.scalars().all()
        return items, total_count

collection_crud = CRUDCollection(Collection)

class CRUDCollectionItem(CRUDBase[CollectionItem, CollectionItemCreate, CollectionItemUpdate]):
    async def add_item_to_collection(
        self, db: AsyncSession, *, obj_in: CollectionItemCreate, collection_id: UUID
    ) -> CollectionItem:
        existing_item = await self.get_item_in_collection(
            db, collection_id=collection_id, content_id=obj_in.content_id
        )
        if existing_item:
            raise ValueError("Content item already exists in this collection.")

        # Logic to determine next sort_order if not provided or to ensure uniqueness
        if obj_in.sort_order is None: # Auto-increment sort_order
            max_sort_order_result = await db.execute(
                select(func.max(CollectionItem.sort_order))
                .filter(CollectionItem.collection_id == collection_id)
            )
            max_sort_order = max_sort_order_result.scalar_one_or_none()
            obj_in.sort_order = (max_sort_order + 1) if max_sort_order is not None else 0
        
        # Else, if sort_order is provided, ensure it's unique for the collection if constraint exists
        # The UniqueConstraint('collection_id', 'sort_order') would handle this at DB level

        db_obj = CollectionItem(
            collection_id=collection_id,
            content_id=obj_in.content_id,
            sort_order=obj_in.sort_order,
            notes=obj_in.notes
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # Eagerly load the associated content for the response
        await db.refresh(db_obj, attribute_names=['content'])
        return db_obj

    async def get_item_in_collection( # Check if specific content is in collection
        self, db: AsyncSession, *, collection_id: UUID, content_id: UUID
    ) -> Optional[CollectionItem]:
        result = await db.execute(
            select(self.model).filter(
                and_(self.model.collection_id == collection_id, self.model.content_id == content_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_collection_item_by_id( # Get specific item by its own ID
        self, db: AsyncSession, item_id: UUID, load_content: bool = True
    ) -> Optional[CollectionItem]:
        query = select(self.model).filter(self.model.id == item_id)
        if load_content:
            query = query.options(joinedload(CollectionItem.content))
        result = await db.execute(query)
        return result.scalar_one_or_none()
        
    async def remove_item_from_collection(
        self, db: AsyncSession, *, item_id: UUID # Remove by CollectionItem.id
    ) -> Optional[CollectionItem]:
        item = await self.get_collection_item_by_id(db, item_id=item_id, load_content=False) # Don't need content to delete
        if item:
            await db.delete(item)
            await db.commit()
            return item # Return the deleted item (or just its ID)
        return None

    async def update_collection_item_details( # Renamed
        self, db: AsyncSession, *, db_item: CollectionItem, obj_in: CollectionItemUpdate
    ) -> CollectionItem:
        # obj_in is CollectionItemUpdate, only has sort_order and notes
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # If sort_order is being changed, you might need logic to re-order other items
        # or validate uniqueness if a DB constraint is not present.
        # For now, direct update.
        
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        await db.refresh(db_item, attribute_names=['content']) # For response
        return db_item
    
    async def get_items_for_collection_paginated(
        self, 
        db: AsyncSession, 
        *, 
        collection_id: UUID, 
        skip: int = 0, 
        limit: int = 10,
        load_content_details: bool = True # Flag to control loading content
    ) -> Tuple[List[CollectionItem], int]:
        
        # Query for total count
        count_query = (
            select(func.count(self.model.id))
            .select_from(self.model)
            .filter(self.model.collection_id == collection_id)
        )
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Query for data
        data_query = (
            select(self.model)
            .filter(self.model.collection_id == collection_id)
            .order_by(self.model.sort_order, self.model.created_at) # Sort by order, then by creation
            .offset(skip)
            .limit(limit)
        )
        
        if load_content_details:
            # Use selectinload for potentially multiple items to avoid N+1 queries
            data_query = data_query.options(selectinload(self.model.content)) 
            
        result = await db.execute(data_query)
        items = result.scalars().all()
        
        return items, total_count

collection_item_crud = CRUDCollectionItem(CollectionItem)