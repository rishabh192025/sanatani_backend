from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

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
        is_featured: Optional[bool] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Place]:
        query = select(self.model)

        if is_featured is not None:
            query = query.where(self.model.is_featured == is_featured)
        if category:
            query = query.where(self.model.category == category)
        if region:
            query = query.where(self.model.region == region)
        if state:
            query = query.where(self.model.state_province == state)
        if country:
            query = query.where(self.model.country == country)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


place_crud = CRUDPlace(Place)
