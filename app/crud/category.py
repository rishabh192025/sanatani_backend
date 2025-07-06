# app/crud/category.py
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload, joinedload

from app.crud.base import CRUDBase
from app.models.category import Category, CategoryScopeType
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.helpers import generate_slug

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    
    async def create_category(self, db: AsyncSession, *, obj_in: CategoryCreate) -> Category:
        slug_to_use = await generate_slug(db, self.model, obj_in.name)

        category_data = obj_in.model_dump(exclude={"slug", "parent_id"})
        
        db_obj = Category(**category_data, slug=slug_to_use)

        if obj_in.parent_id:
            try:
                parent_uuid = PyUUID(obj_in.parent_id)
                # Optional: Check if parent_id exists and is a valid category
                parent_category = await self.get(db, id=parent_uuid)
                if not parent_category:
                    raise ValueError(f"Parent category with ID {obj_in.parent_id} not found.")
                db_obj.parent_id = parent_uuid
            except ValueError: 
                 raise ValueError(f"Invalid parent_id format: {obj_in.parent_id}.")
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_category_by_slug(self, db: AsyncSession, *, slug: str) -> Optional[Category]:
        result = await db.execute(select(Category).filter(Category.slug == slug)).filter(Category.is_deleted.is_(False))
        return result.scalar_one_or_none()

    async def get_categories_by_type( # Assuming 'scope' is your 'type'
        self, 
        db: AsyncSession, 
        *, 
        type: str, # Use your enum type
        #skip: int = 0, 
        #limit: int = 100,
        parent_id: Optional[PyUUID] = None,
        #load_children: bool = False, # Defaulting to True for this example to fix the error
    ) -> Tuple[List[Category], int]:
        
        # Build filters
        filters = [Category.type == type] # Use your actual column name ('type' or 'scope')
        if parent_id is not None:
            filters.append(Category.parent_id == parent_id)
        # If parent_id is None, it correctly fetches top-level categories for that scope.

        
        # Count query
        count_query = select(func.count(Category.id)).select_from(Category).where(Category.is_deleted.is_(False))
        if filters:
            count_query = count_query.where(*filters)
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Data query
        data_query = select(Category).where(Category.is_deleted.is_(False))
        if filters:
            data_query = data_query.where(*filters)
        

        # if load_children:
        #     data_query = data_query.options(selectinload(Category.children))

        data_query = data_query.order_by(Category.sort_order, Category.name)
        
        data_result = await db.execute(data_query)
        items = data_result.scalars().unique().all() # .unique() is good with selectinload
        
        return items, total_count

    async def get_category_with_children(self, db: AsyncSession, category_id: PyUUID) -> Optional[Category]:
        result = await db.execute(
            select(Category)
            .options(
                selectinload(Category.children) # Load direct children
                # If you need to go deeper, chain selectinload or joinedload:
                # .selectinload(Category.children).selectinload(Category.children) # For 2 levels
            )
            .filter(Category.id == category_id)
            .filter(Category.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()
        
    async def update_category(
        self, db: AsyncSession, *, db_obj: Category, obj_in: CategoryUpdate
    ) -> Category:
        update_data = obj_in.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"] != db_obj.slug:
            existing_slug = await self.get_category_by_slug(db, slug=update_data["slug"])
            if existing_slug and existing_slug.id != db_obj.id:
                raise ValueError(f"Slug '{update_data['slug']}' already exists.")
        
        if "parent_id" in update_data:
            if update_data["parent_id"] is None:
                db_obj.parent_id = None # Make it top-level
            else:
                try:
                    parent_uuid = PyUUID(update_data["parent_id"])
                    if parent_uuid == db_obj.id:
                        raise ValueError("Category cannot be its own parent.")
                    # Optional: Check if new parent exists
                    parent_category = await self.get(db, id=parent_uuid)
                    if not parent_category:
                         raise ValueError(f"New parent category with ID {parent_uuid} not found.")
                    # Optional: Check for circular dependencies if reparenting
                    db_obj.parent_id = parent_uuid
                except ValueError:
                    raise ValueError(f"Invalid parent_id format: {update_data['parent_id']}.")
            del update_data["parent_id"] # Remove so generic update doesn't try to set it as string

        return await super().update(db=db, db_obj=db_obj, obj_in=update_data) # Pass dict

category_crud = CRUDCategory(Category)