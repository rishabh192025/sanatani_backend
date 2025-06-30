from uuid import UUID
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Tuple

from app.models import ChatWithGuruji
from app.schemas import ChatWithGurujiCreate, ChatWithGurujiUpdate
from app.crud.base import CRUDBase
# from app.utils.helpers import generate_slug


class CRUDChatWithGuruji(CRUDBase[ChatWithGuruji, ChatWithGurujiCreate, ChatWithGurujiUpdate]):
    async def create_chat_with_guruji(self, db: AsyncSession, *, obj_in: ChatWithGurujiCreate, user_id: UUID) -> ChatWithGuruji:
        obj_in_data = obj_in.model_dump()       # preserves native Python types datetime.date, UUID, etc.
        obj_in_data["user_id"] = UUID(user_id) if isinstance(user_id, str) else user_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_by_chat_id(self, db: AsyncSession, chat_id: str) -> Optional[ChatWithGuruji]:
        result = await db.execute(select(self.model).where(self.model.chat_id == chat_id))
        return result.scalar_one_or_none()


    async def get_filtered_with_count(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ChatWithGuruji], int]:
        filters = []

        count_query = select(func.count(self.model.id)).where(*filters)
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = select(self.model).where(*filters).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(data_query)
        items = result.scalars().all()

        return items, total_count

    async def delete_chat(self, db: AsyncSession, chat_id: str) -> Optional[ChatWithGuruji]:
        # For async, db.get is not directly available, so we fetch first
        obj = await self.get_by_chat_id(db, chat_id=chat_id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj


chat_with_guruji_crud = CRUDChatWithGuruji(ChatWithGuruji)

