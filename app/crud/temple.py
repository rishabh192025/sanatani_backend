from uuid import UUID
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Tuple

from app.models import Temple
from app.schemas import TempleCreate, TempleUpdate
from app.crud.base import CRUDBase


class CRUDTemple(CRUDBase[Temple, TempleCreate, TempleUpdate]):
    async def create_temple(self, db: AsyncSession, *, obj_in: TempleCreate, created_by: UUID) -> Temple:
        obj_in_data = obj_in.model_dump()  # preserves native Python types datetime.date, UUID, etc.
        obj_in_data["created_by"] = UUID(created_by) if isinstance(created_by, str) else created_by
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Temple]:
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalar_one_or_none()


    async def get_filtered_with_count(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100,
            name: Optional[str] = None,
    ) -> Tuple[List[Temple], int]:
        filters = []
        if name is not None:
            try:
                filters.append(func.lower(self.model.name).ilike(f"%{name.lower()}%"))
            except KeyError: pass

        count_query = select(func.count(self.model.id)).where(*filters)
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = select(self.model).where(*filters).offset(skip).limit(limit)
        result = await db.execute(data_query)
        items = result.scalars().all()

        return items, total_count

    async def get_temples_count(self, db: AsyncSession) -> int:
        count_query = select(func.count(self.model.id))
        result = await db.execute(count_query)
        return result.scalar_one()
        
    # async def get_filtered(
    #         self,
    #         db: AsyncSession,
    #         name: Optional[str] = None,
    #         skip: int = 0,
    #         limit: int = 100,
    # ) -> List[Temple]:
    #     query = select(self.model)
    #
    #     if name is not None:
    #         # query = query.where(self.model.name == name)
    #         query = query.where(func.lower(self.model.name).ilike(f"%{name.lower()}%"))       # added ILIKE if asked to remove uncomment above one
    #     query = query.offset(skip).limit(limit)
    #     result = await db.execute(query)
    #     return result.scalars().all()


temple_crud = CRUDTemple(Temple)