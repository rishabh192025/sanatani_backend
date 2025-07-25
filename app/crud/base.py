# app/crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID as PyUUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from sqlalchemy.future import select # Changed for SQLAlchemy 1.4+ style with async
from sqlalchemy.orm import selectinload
from sqlalchemy import func, update as sqlalchemy_update, delete as sqlalchemy_delete
from app.models.content import BookChapter, BookSection, Content, ContentSubType
from app.database import Base # Assuming Base is defined in app.database

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Union[PyUUID, int, str]) -> Optional[ModelType]:
        result = await db.execute(
                select(self.model)
                .filter(self.model.id == id)
                .filter(self.model.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.is_deleted.is_(False))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_count(self, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count(self.model.id))
            .filter(self.model.is_deleted.is_(False))
        )
        return result.scalar_one()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj) # Current state of db_obj
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Use model_dump for Pydantic v2, exclude_unset=True to only update provided fields
            update_data = obj_in.model_dump(exclude_unset=True) 
        
        for field in obj_data: # Iterate over fields of the model object
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj) # Add the modified object to the session
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Union[PyUUID, int, str]) -> Optional[ModelType]:
        # For async, db.get is not directly available, so we fetch first
        obj = await self.get(db, id=id)
        if obj:
            obj.is_deleted = True
            # await db.delete(obj)
            await db.commit()
            await db.refresh(obj)  # Refresh to re-fetch any auto-updated fields (optional)

        return obj

    async def get_book_table_of_contents(self, db: AsyncSession, book_id: PyUUID) -> Optional[Content]:
        """
        Fetches a book with its chapters, and each chapter with its sections,
        optimized for a table of contents view.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.chapters) # Content.chapters
                .selectinload(BookChapter.sections) # BookChapter.sections
            )
            .filter(self.model.id == book_id)
            .filter(self.model.sub_type == ContentSubType.BOOK.value) # Ensure it's a book
            .filter(self.model.is_deleted.is_(False))
        )
        book = result.scalar_one_or_none()
        # The relationships (chapters and their sections) will be loaded.
        # Pydantic schemas (TOCChapterItem, TOCSectionItem) will select only needed fields.
        return book