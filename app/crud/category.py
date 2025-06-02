# app/crud/category.py (New File - Placeholder if needed later)
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.category import Category # Assuming you have this model
from app.schemas.category import CategoryCreate, CategoryUpdate # Create these schemas

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    
    async def get_category_by_slug(self, db: AsyncSession, *, slug: str) -> Optional[Category]:
        result = await db.execute(select(Category).filter(Category.slug == slug))
        return result.scalar_one_or_none()

    async def get_featured_categories(self, db: AsyncSession, limit: int = 5) -> List[Category]:
        # This assumes your Category model has an 'is_featured' boolean field
        # and possibly a 'sort_order' field.
        # Modify query as needed.
        # For now, let's assume there's no 'is_featured' field and just return top-level categories.
        result = await db.execute(
            select(Category)
            .filter(Category.parent_id == None) # Example: get top-level categories
            .order_by(Category.sort_order, Category.name)
            .limit(limit)
        )
        return result.scalars().all()

    # Add other specific category methods as needed

category_crud = CRUDCategory(Category)