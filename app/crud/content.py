# app/crud/content.py
from typing import List, Optional, Tuple
from sqlalchemy import func
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.crud.base import CRUDBase
from app.models.content import (
    Content, 
    ContentType as ContentTypeEnum, 
    LanguageCode as LanguageCodeEnum, 
    ContentSubType,
    ContentStatus
)
from app.schemas.book import BookCreate, BookUpdate
from app.utils.helpers import generate_slug  # Assuming a helper for slug
from sqlalchemy.orm import selectinload

class ContentCRUD(CRUDBase[Content, BookCreate, BookUpdate]):
    async def get_content(self, db: AsyncSession, content_id: PyUUID) -> Optional[Content]:
        query = select(self.model).filter(self.model.id == content_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_content_by_slug(self, db: AsyncSession, slug: str) -> Optional[Content]:
        query = select(self.model).filter(self.model.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()

content_crud = ContentCRUD(Content)