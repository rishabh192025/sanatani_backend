# app/crud/bookmark.py
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload, joinedload

from app.crud.base import CRUDBase
from app.models.user_bookmark import UserBookmark # Ensure this is the correct model name
from app.models.content import Content # For joining
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate

class CRUDBookmark(CRUDBase[UserBookmark, BookmarkCreate, BookmarkUpdate]):

    async def create_bookmark(
        self, db: AsyncSession, *, obj_in: BookmarkCreate, user_id: PyUUID
    ) -> UserBookmark:
        # Check if content exists (optional, depends on FK constraints handling it)
        content_exists = await db.execute(select(Content.id).where(Content.id == obj_in.content_id))
        if not content_exists.scalar_one_or_none():
            raise ValueError("Content to bookmark does not exist.")

        # Check for existing bookmark (UniqueConstraint should handle this at DB level,
        # but a check here provides a cleaner error)
        existing = await self.get_by_user_and_content(db, user_id=user_id, content_id=obj_in.content_id)
        if existing:
            # Optionally, update notes if it already exists, or raise error
            # For now, let's assume creating a duplicate is an error (handled by DB constraint)
            # Or you can return the existing one: return existing
            raise ValueError("Content already bookmarked by this user.")

        db_obj = UserBookmark(
            user_id=user_id,
            content_id=obj_in.content_id,
            notes=obj_in.notes
            # bookmark_type will use its default 'content'
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user_and_content(
        self, db: AsyncSession, *, user_id: PyUUID, content_id: PyUUID
    ) -> Optional[UserBookmark]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id, self.model.content_id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_user_bookmarks_paginated(
        self, db: AsyncSession, *, user_id: PyUUID, skip: int = 0, limit: int = 10
    ) -> Tuple[List[UserBookmark], int]:
        
        count_query = (
            select(func.count(self.model.id))
            .select_from(self.model)
            .filter(self.model.user_id == user_id)
        )
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        data_query = (
            select(self.model)
            .options(joinedload(self.model.content)) # Eager load content details
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(data_query)
        items = result.scalars().all()
        return items, total_count

    async def remove_bookmark(
        self, db: AsyncSession, *, user_id: PyUUID, content_id: PyUUID
    ) -> bool:
        bookmark = await self.get_by_user_and_content(db, user_id=user_id, content_id=content_id)
        if bookmark:
            await db.delete(bookmark)
            await db.commit()
            return True
        return False

bookmark_crud = CRUDBookmark(UserBookmark)