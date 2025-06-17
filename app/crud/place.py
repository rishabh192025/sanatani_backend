# app/crud/place.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID
from app.models import Place
from app.schemas import PlaceCreate, PlaceUpdate
from app.crud.base import CRUDBase


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Place]:
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        db: AsyncSession,
        name: Optional[str] = None,
        is_featured: Optional[bool] = None,
        category_id: Optional[UUID] = None,
        region_id: Optional[UUID] = None,
        state_id: Optional[UUID] = None,
        country_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Place]:
        query = select(self.model)

        if name is not None:
            query = query.where(self.model.name == name)
        if is_featured is not None:
            query = query.where(self.model.is_featured == is_featured)
        if category_id is not None:
            query = query.where(self.model.category_id == category_id)
        if region_id is not None:
            query = query.where(self.model.region_id == region_id)
        if state_id is not None:
            query = query.where(self.model.state_id == state_id)
        if country_id is not None:
            query = query.where(self.model.country_id == country_id)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


place_crud = CRUDPlace(Place)
