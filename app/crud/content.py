# app/crud/content.py
from typing import List, Optional, Union
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.crud.base import CRUDBase
from app.models.content import Content, ContentType as ContentTypeEnum, LanguageCode as LanguageCodeEnum
from app.schemas.content import ContentCreate, ContentUpdate
from app.utils.helpers import generate_slug # Assuming a helper for slug

class CRUDContent(CRUDBase[Content, ContentCreate, ContentUpdate]):

    async def get_content(self, db: AsyncSession, content_id: PyUUID) -> Optional[Content]:
        return await super().get(db, id=content_id)

    async def create_content(self, db: AsyncSession, *, obj_in: ContentCreate, author_id: PyUUID) -> Content:
        # Use a robust slug generation utility
        slug = await generate_slug(db, self.model, obj_in.title)

        content_data = obj_in.model_dump(exclude={"category_id"}) # Exclude if handled separately
        
        db_obj = Content(
            **content_data,
            author_id=author_id,
            slug=slug
        )
        if obj_in.category_id:
            try:
                # Here, you might want to fetch and validate the category object
                # For simplicity, just assigning the UUID if provided as string
                db_obj.category_id = PyUUID(obj_in.category_id)
            except ValueError:
                # Handle invalid UUID for category_id appropriately
                # e.g., raise HTTPException or log warning
                pass 

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_content_list(
        self, db: AsyncSession, *, 
        skip: int = 0, limit: int = 10,
        content_type_str: Optional[str] = None, # Renamed to avoid clash with model enum
        category_id_str: Optional[str] = None, 
        language_str: Optional[str] = None,
        status_str: Optional[str] = None, # Added status filter
        search_query: Optional[str] = None # Added search filter
    ) -> List[Content]:
        query = select(Content)
        
        if content_type_str:
            try:
                # Assuming ContentTypeEnum is the Python Enum from your models
                ct_enum_val = ContentTypeEnum[content_type_str.upper()]
                query = query.where(Content.content_type == ct_enum_val)
            except KeyError:
                pass 
        if category_id_str:
            try:
                cat_uuid = PyUUID(category_id_str)
                query = query.where(Content.category_id == cat_uuid)
            except ValueError:
                pass
        if language_str:
            try:
                lang_enum_val = LanguageCodeEnum[language_str.upper()]
                query = query.where(Content.language == lang_enum_val)
            except KeyError:
                pass
        if status_str:
            from app.models.content import ContentStatus # Local import
            try:
                status_enum_val = ContentStatus[status_str.upper()]
                query = query.where(Content.status == status_enum_val)
            except KeyError:
                pass
        
        if search_query:
            # Basic search on title and description
            # For more advanced search, consider PostgreSQL full-text search or Elasticsearch
            search_term = f"%{search_query}%"
            query = query.where(
                or_(
                    Content.title.ilike(search_term),
                    Content.description.ilike(search_term)
                )
            )
        
        query = query.order_by(Content.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_content_by_slug(self, db: AsyncSession, slug: str) -> Optional[Content]:
        result = await db.execute(select(Content).filter(Content.slug == slug))
        return result.scalar_one_or_none()

content_crud = CRUDContent(Content)