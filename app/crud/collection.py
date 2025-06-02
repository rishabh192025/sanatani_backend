# app/crud/collection.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.collection import Collection, CollectionItem
from app.schemas.collection import CollectionCreate, CollectionUpdate, CollectionItemCreate, CollectionItemUpdate
from app.utils.helpers import generate_slug # Assuming you have this

# --- CRUD FOR COLLECTION ---
class CRUDCollection(CRUDBase[Collection, CollectionCreate, CollectionUpdate]):
    async def create_collection(self, db: AsyncSession, *, obj_in: CollectionCreate) -> Collection:
        slug = await generate_slug(db, self.model, obj_in.name) # Generate unique slug
        collection_data = obj_in.model_dump()
        
        db_obj = Collection(**collection_data, slug=slug)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_collection_by_slug(self, db: AsyncSession, slug: str, load_items: bool = False) -> Optional[Collection]:
        query = select(self.model).filter(self.model.slug == slug)
        if load_items:
            query = query.options(
                selectinload(self.model.items).options(
                    joinedload(CollectionItem.content_item) # Also load content details for each item
                ) 
            )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_collection(self, db: AsyncSession, id: UUID, load_items: bool = False) -> Optional[Collection]:
        query = select(self.model).filter(self.model.id == id)
        if load_items:
            query = query.options(
                selectinload(self.model.items).options(
                    joinedload(CollectionItem.content_item) # Load content details
                )
            )
        result = await db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_all_collections(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, is_public: Optional[bool] = None, is_featured: Optional[bool] = None
    ) -> List[Collection]:
        query = select(self.model)
        if is_public is not None:
            query = query.filter(self.model.is_public == is_public)
        if is_featured is not None:
            query = query.filter(self.model.is_featured == is_featured)
        
        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

collection_crud = CRUDCollection(Collection)

# --- CRUD FOR COLLECTION ITEM ---
class CRUDCollectionItem(CRUDBase[CollectionItem, CollectionItemCreate, CollectionItemUpdate]):
    async def add_item_to_collection(
        self, db: AsyncSession, *, collection_id: UUID, content_id: UUID, obj_in: CollectionItemCreate
    ) -> CollectionItem:
        # Check if item already exists in collection
        existing_item = await self.get_item_in_collection(db, collection_id=collection_id, content_id=content_id)
        if existing_item:
            raise ValueError("Content item already exists in this collection.")

        db_obj = CollectionItem(
            collection_id=collection_id,
            content_id=content_id, # content_id from obj_in is now path param
            sort_order=obj_in.sort_order,
            notes=obj_in.notes
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # Optionally load content_detail for response
        await db.refresh(db_obj, attribute_names=['content_item'])
        return db_obj

    async def get_item_in_collection(
        self, db: AsyncSession, *, collection_id: UUID, content_id: UUID
    ) -> Optional[CollectionItem]:
        result = await db.execute(
            select(self.model).filter(
                and_(self.model.collection_id == collection_id, self.model.content_id == content_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_collection_item_by_id(self, db: AsyncSession, item_id: UUID) -> Optional[CollectionItem]:
        result = await db.execute(
            select(self.model).options(joinedload(CollectionItem.content_item)).filter(self.model.id == item_id)
        )
        return result.scalar_one_or_none()
        
    async def remove_item_from_collection(
        self, db: AsyncSession, *, collection_id: UUID, item_id: UUID # Using item_id now
    ) -> Optional[CollectionItem]:
        item = await self.get_collection_item_by_id(db, item_id=item_id)
        if item and item.collection_id == collection_id:
            await db.delete(item)
            await db.commit()
            return item
        return None

    async def update_collection_item(
        self, db: AsyncSession, *, item_id: UUID, obj_in: CollectionItemUpdate
    ) -> Optional[CollectionItem]:
        db_item = await self.get_collection_item_by_id(db, item_id=item_id)
        if not db_item:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        await db.refresh(db_item, attribute_names=['content_item']) # Refresh relation
        return db_item

collection_item_crud = CRUDCollectionItem(CollectionItem)