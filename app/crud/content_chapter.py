# app/crud/content_chapter.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.content import ContentChapter
from app.schemas.content_chapter import ContentChapterCreate, ContentChapterUpdate

class CRUDContentChapter(CRUDBase[ContentChapter, ContentChapterCreate, ContentChapterUpdate]):
    
    async def create_with_content_id(
        self, db: AsyncSession, *, obj_in: ContentChapterCreate, content_id: UUID
    ) -> ContentChapter:
        # Check for duplicate chapter number for this content_id
        existing_chapter = await self.get_by_content_and_chapter_number(
            db, content_id=content_id, chapter_number=obj_in.chapter_number
        )
        if existing_chapter:
            # Or handle this as an update, or raise a more specific error
            raise ValueError(f"Chapter number {obj_in.chapter_number} already exists for this content.")

        db_obj = ContentChapter(**obj_in.model_dump(), content_id=content_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_chapters_by_content_id(
        self, db: AsyncSession, *, content_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ContentChapter]:
        result = await db.execute(
            select(self.model)
            .filter(ContentChapter.content_id == content_id)
            .order_by(ContentChapter.chapter_number)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_content_and_chapter_number(
        self, db: AsyncSession, *, content_id: UUID, chapter_number: int
    ) -> Optional[ContentChapter]:
        result = await db.execute(
            select(self.model).filter(
                and_(
                    ContentChapter.content_id == content_id,
                    ContentChapter.chapter_number == chapter_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_chapter(
        self, db: AsyncSession, *, chapter_id: UUID
    ) -> Optional[ContentChapter]:
        return await self.get(db, id=chapter_id)

content_chapter_crud = CRUDContentChapter(ContentChapter)