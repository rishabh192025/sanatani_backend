# app/crud/crud_sacred_place.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID

from app.models import SacredPlace
from app.schemas import SacredPlaceCreate, SacredPlaceUpdate, PlaceType
from app.crud.base import CRUDBase


class CRUDSacredPlace(CRUDBase[SacredPlace, SacredPlaceCreate, SacredPlaceUpdate]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[SacredPlace]:
        result = await db.execute(select(self.model).where(self.model.place_name == name))
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        db: AsyncSession,
        country: Optional[str] = None,
        place_type: Optional[PlaceType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SacredPlace]:
        query = select(self.model)

        if country:
            query = query.where(self.model.country == country)
        if place_type:
            query = query.where(self.model.categories == place_type)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


sacred_place_crud = CRUDSacredPlace(SacredPlace)
