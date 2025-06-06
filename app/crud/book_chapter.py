# app/crud/book_chapter.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.content import BookChapter # Using the specific BookChapter model
from app.schemas.book_chapter import BookChapterCreate, BookChapterUpdate

class CRUDBookChapter(CRUDBase[BookChapter, BookChapterCreate, BookChapterUpdate]):
    
    async def create_for_book(
        self, db: AsyncSession, *, obj_in: BookChapterCreate, book_id: UUID # book_id is content_id
    ) -> BookChapter:
        # Logic to ensure chapter_number is unique for this book_id
        existing_chapter_num = await self.get_by_book_and_chapter_number(
            db, book_id=book_id, chapter_number=obj_in.chapter_number
        )
        if existing_chapter_num:
            raise ValueError(f"Chapter number {obj_in.chapter_number} already exists for this book.")

        db_obj = BookChapter(
            **obj_in.model_dump(), 
            book_id=book_id # Map book_id to content_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_chapters_for_book(
        self, db: AsyncSession, *, book_id: UUID, skip: int = 0, limit: int = 100, load_sections: bool = False
    ) -> List[BookChapter]:
        query = (
            select(self.model)
            .filter(BookChapter.book_id == book_id)
            .order_by(BookChapter.chapter_number)
            .offset(skip)
            .limit(limit)
        )
        if load_sections:
            query = query.options(selectinload(self.model.sections))
            
        result = await db.execute(query)
        return result.scalars().all()

    async def get_chapter_by_id(
        self, db: AsyncSession, *, chapter_id: UUID, book_id: Optional[UUID] = None, load_sections: bool = False
    ) -> Optional[BookChapter]:
        query = select(self.model).filter(self.model.id == chapter_id)
        if book_id: # Optional: ensure it belongs to a specific book
            query = query.filter(self.model.book_id == book_id)
        
        if load_sections:
            query = query.options(selectinload(self.model.sections))
            
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_book_and_chapter_number(
        self, db: AsyncSession, *, book_id: UUID, chapter_number: int
    ) -> Optional[BookChapter]:
        result = await db.execute(
            select(self.model).filter(
                and_(
                    BookChapter.book_id == book_id,
                    BookChapter.chapter_number == chapter_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_chapter(
        self, db: AsyncSession, *, db_obj: BookChapter, obj_in: BookChapterUpdate
    ) -> BookChapter:
        # Handle chapter_number change and potential collision
        if obj_in.chapter_number is not None and obj_in.chapter_number != db_obj.chapter_number:
            existing_chapter_num = await self.get_by_book_and_chapter_number(
                db, book_id=db_obj.book_id, chapter_number=obj_in.chapter_number
            )
            if existing_chapter_num and existing_chapter_num.id != db_obj.id:
                raise ValueError(f"Chapter number {obj_in.chapter_number} already exists for this book.")
        
        # Use the generic update from CRUDBase
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)


book_chapter_crud = CRUDBookChapter(BookChapter)