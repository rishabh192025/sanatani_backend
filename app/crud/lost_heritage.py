from uuid import UUID
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Tuple

from app.models import LostHeritage
from app.schemas import LostHeritageCreate, LostHeritageUpdate
from app.crud.base import CRUDBase


class CRUDLostHeritage(CRUDBase[LostHeritage, LostHeritageCreate, LostHeritageUpdate]):
    async def create_lost_heritage(self, db: AsyncSession, *, obj_in: LostHeritageCreate, created_by: UUID) -> LostHeritage:
        obj_in_data = obj_in.model_dump()       # preserves native Python types datetime.date, UUID, etc.
        obj_in_data["created_by"] = UUID(created_by) if isinstance(created_by, str) else created_by
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[LostHeritage]:
        result = await db.execute(
            select(self.model).where(
                self.model.title == title,
                self.model.is_deleted.is_(False)
            )
        )
        return result.scalar_one_or_none()

    async def get_filtered_with_count(
            self,
            db: AsyncSession,
            title: Optional[str] = None,
            skip: int = 0,
            limit: int = 100,
    ) -> Tuple[List[LostHeritage], int]:
        filters = []
        if title:
            filters.append(func.lower(self.model.title).ilike(f"%{title.lower()}%"))

        count_query = select(func.count(self.model.id)).where(*filters, self.model.is_deleted.is_(False))
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = (select(self.model).where(*filters, self.model.is_deleted.is_(False)).offset(skip).limit(limit))
        result = await db.execute(data_query)
        items = result.scalars().all()

        return items, total_count


    # async def get_filtered(
    #         self,
    #         db: AsyncSession,
    #         title: Optional[str] = None,
    #         skip: int = 0,
    #         limit: int = 100,
    # ) -> List[LostHeritage]:
    #     query = select(self.model)
    #
    #     if title is not None:
    #         # query = query.where(self.model.title == title)
    #         query = query.where(func.lower(self.model.title).ilike(f"%{title.lower()}%"))       # added ILIKE if asked to remove uncomment above one
    #     query = query.offset(skip).limit(limit)
    #     result = await db.execute(query)
    #     return result.scalars().all()


lost_heritage_crud = CRUDLostHeritage(LostHeritage)