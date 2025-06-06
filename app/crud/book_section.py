# app/crud/book_section.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.content import BookSection # Using specific BookSection model
from app.schemas.book_section import BookSectionCreate, BookSectionUpdate

class CRUDBookSection(CRUDBase[BookSection, BookSectionCreate, BookSectionUpdate]):
    
    async def create_for_chapter(
        self, db: AsyncSession, *, obj_in: BookSectionCreate, chapter_id: UUID
    ) -> BookSection:
        # Ensure obj_in doesn't try to set chapter_id from payload if it was added to base schema
        # section_data = obj_in.model_dump(exclude={'chapter_id'} if 'chapter_id' in obj_in.__fields__ else None)
        section_data = obj_in.model_dump() # chapter_id is not in BookSectionCreate base

        # Logic to ensure section_order is unique for this chapter_id
        existing_section_order = await self.get_by_chapter_and_order(
             db, chapter_id=chapter_id, section_order=section_data.get("section_order", 0)
        )
        if existing_section_order:
            raise ValueError(f"Section order {section_data.get('section_order', 0)} already exists for this chapter.")

        db_obj = BookSection(**section_data, chapter_id=chapter_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_sections_for_chapter(
        self, db: AsyncSession, *, chapter_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[BookSection]:
        result = await db.execute(
            select(self.model)
            .filter(BookSection.chapter_id == chapter_id)
            .order_by(BookSection.section_order)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_section_by_id(
        self, db: AsyncSession, *, section_id: UUID, chapter_id: Optional[UUID] = None
    ) -> Optional[BookSection]:
        query = select(self.model).filter(self.model.id == section_id)
        if chapter_id:
            query = query.filter(self.model.chapter_id == chapter_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_chapter_and_order(
        self, db: AsyncSession, *, chapter_id: UUID, section_order: int
    ) -> Optional[BookSection]:
        result = await db.execute(
            select(self.model).filter(
                and_(
                    BookSection.chapter_id == chapter_id,
                    BookSection.section_order == section_order
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_section(
        self, db: AsyncSession, *, db_obj: BookSection, obj_in: BookSectionUpdate # Or BookSectionUpdatePayload
    ) -> BookSection:
        # Handle section_order change and potential collision
        # Assuming obj_in is now BookSectionUpdatePayload which doesn't have chapter_id
        update_data = obj_in.model_dump(exclude_unset=True)

        if "section_order" in update_data and update_data["section_order"] != db_obj.section_order:
            existing_section_order = await self.get_by_chapter_and_order(
                db, chapter_id=db_obj.chapter_id, section_order=update_data["section_order"]
            )
            if existing_section_order and existing_section_order.id != db_obj.id:
                raise ValueError(f"Section order {update_data['section_order']} already exists for this chapter.")
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data) # Pass dict to base update

book_section_crud = CRUDBookSection(BookSection)