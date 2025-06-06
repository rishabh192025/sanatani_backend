# app/crud/content_section.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.content import ContentSection # Assuming ContentSection is in content.py
from app.schemas.content_section import ContentSectionCreate, ContentSectionUpdate

class CRUDContentSection(CRUDBase[ContentSection, ContentSectionCreate, ContentSectionUpdate]):
    
    async def create_with_chapter_id(
        self, db: AsyncSession, *, obj_in: ContentSectionCreate, chapter_id: UUID
    ) -> ContentSection:
        # Optional: Check for duplicate section_order for this chapter_id
        existing_section_order = await self.get_by_chapter_and_order(
            db, chapter_id=chapter_id, section_order=obj_in.section_order
        )
        if existing_section_order:
            # Handle this: re-order, increment others, or raise error
            # For simplicity, raising an error or appending currently.
            # A more robust solution would be to shift orders or find next available.
            # Or simply allow duplicate orders and rely on primary key for uniqueness.
            # The UniqueConstraint in the model will prevent duplicates if strict.
            # Let's assume for now, if order exists, we just create.
            # The UniqueConstraint ('chapter_id', 'section_order') will catch it if it's an issue.
            pass

        db_obj = ContentSection(**obj_in.model_dump(), chapter_id=chapter_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_sections_by_chapter_id(
        self, db: AsyncSession, *, chapter_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ContentSection]:
        result = await db.execute(
            select(self.model)
            .filter(ContentSection.chapter_id == chapter_id)
            .order_by(ContentSection.section_order)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_section(
        self, db: AsyncSession, *, section_id: UUID
    ) -> Optional[ContentSection]:
        return await self.get(db, id=section_id)

    async def get_by_chapter_and_order(
        self, db: AsyncSession, *, chapter_id: UUID, section_order: int
    ) -> Optional[ContentSection]:
        result = await db.execute(
            select(self.model).filter(
                and_(
                    ContentSection.chapter_id == chapter_id,
                    ContentSection.section_order == section_order
                )
            )
        )
        return result.scalar_one_or_none()

content_section_crud = CRUDContentSection(ContentSection)