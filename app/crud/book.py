# app/crud/book.py
from typing import List, Optional
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

# Assuming BookType enum exists in app.schemas.book
from app.schemas.book import BookType


class CRUDBook(CRUDBase[Content, BookCreate, BookUpdate]):
    
    async def get_book(self, db: AsyncSession, content_id: PyUUID) -> Optional[Content]:
        query = select(self.model).filter(self.model.id == content_id)
        # Use .value to convert enum to string if Content.content_type stores string values in DB
        query = query.where(Content.content_type == ContentTypeEnum.BOOK.value)  # If book_type=TEXT
        # query = query.where(Content.sub_type == ContentSubType.BOOK.value)  # This is good for your plan
        # For audio books, it would be:
        # query = query.where(Content.content_type == ContentTypeEnum.AUDIO.value)
        # query = query.where(Content.sub_type == ContentSubType.BOOK.value)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_book(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: BookCreate, 
        author_id: PyUUID
    ) -> Content:
        slug = await generate_slug(db, self.model, obj_in.title)
        content_data = obj_in.model_dump(exclude={"category_id", "book_type"})

        # Convert book_type string to enum safely (case insensitive)
        try:
            book_type_enum = BookType(obj_in.book_type.lower())
        except Exception:
            book_type_enum = BookType.TEXT  # default fallback

        # Set content_type based on book_type
        if book_type_enum == BookType.AUDIO:
            determined_content_type = ContentTypeEnum.AUDIO.value
        elif book_type_enum == BookType.PDF:
            # Assuming you want a new enum value for PDFs; create or reuse
            # For example:
            determined_content_type = ContentTypeEnum.PDF.value  # <-- make sure this exists
        else:
            # Default to text book
            determined_content_type = ContentTypeEnum.BOOK.value

        db_obj = Content(
            **content_data,
            content_type=determined_content_type,
            sub_type=ContentSubType.BOOK.value,
            author_id=author_id,
            slug=slug
        )

        if obj_in.category_id:
            try:
                db_obj.category_id = PyUUID(obj_in.category_id)
            except ValueError:
                pass

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    

    async def get_book_list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 10,
        # book_type_filter: Optional[BookType] = None,  # New filter based on BookType
        category_id_str: Optional[str] = None,
        language_str: Optional[str] = None,
        status_str: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Content]:
        query = select(Content)
        query = query.where(Content.sub_type == ContentSubType.BOOK.value)  # Core filter for all books

        # if book_type_filter:
        #     if book_type_filter == BookType.TEXT:
        #         query = query.where(Content.content_type == ContentTypeEnum.BOOK.value)
        #     elif book_type_filter == BookType.AUDIO:
        #         query = query.where(Content.content_type == ContentTypeEnum.AUDIO.value)

        if category_id_str:
            try:
                cat_uuid = PyUUID(category_id_str)
                query = query.where(Content.category_id == cat_uuid)
            except ValueError:
                pass

        if language_str:
            try:
                lang_enum_val = LanguageCodeEnum[language_str.upper()].value
                query = query.where(Content.language == lang_enum_val)
            except KeyError:
                pass

        if status_str:
            try:
                status_enum_val = ContentStatus[status_str.upper()].value
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

    async def get_book_by_slug(
        self, 
        db: AsyncSession, 
        slug: str
    ) -> Optional[Content]:
        query = select(self.model).filter(self.model.slug == slug)
        query = query.where(Content.sub_type == ContentSubType.BOOK.value)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_book_with_chapters(
        self, 
        db: AsyncSession, 
        content_id: PyUUID
    ) -> Optional[Content]:
        query = (
            select(self.model)
            .options(selectinload(self.model.chapters))
            .filter(self.model.id == content_id)
        )
        query = query.where(Content.sub_type == ContentSubType.BOOK.value)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_book_by_slug_with_chapters(
        self, 
        db: AsyncSession, 
        slug: str
    ) -> Optional[Content]:
        query = (
            select(self.model)
            .options(selectinload(self.model.chapters))
            .filter(self.model.slug == slug)
        )
        query = query.where(Content.sub_type == ContentSubType.BOOK.value)
        result = await db.execute(query)
        return result.scalar_one_or_none()


book_crud = CRUDBook(Content)
