# app/crud/place.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Tuple
from uuid import UUID
from app.models import Place
from app.schemas import PlaceCreate, PlaceUpdate
from app.crud.base import CRUDBase
from sqlalchemy import func


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    async def create_place(self, db: AsyncSession, *, obj_in: PlaceCreate, created_by: UUID) -> Place:
        obj_in_data = obj_in.model_dump()       # preserves native Python types datetime.date, UUID, etc.
        obj_in_data["created_by"] = UUID(created_by) if isinstance(created_by, str) else created_by
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Place]:
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> List[Place]:
        result = await db.execute(select(self.model))
        return result.scalars().all()

    async def get_filtered_with_count(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100,
            name: Optional[str] = None,
            is_featured: Optional[bool] = None,
            category_id: Optional[UUID] = None,
            region_id: Optional[UUID] = None,
            state_id: Optional[UUID] = None,
            country_id: Optional[UUID] = None,
    ) -> Tuple[List[Place], int]:
        filters = []
        if name is not None:
            try:
                filters.append(func.lower(self.model.name).ilike(f"%{name.lower()}%"))
            except KeyError: pass
        if is_featured is not None:
            try:
                filters.append(self.model.is_featured == is_featured)
            except KeyError: pass
        if category_id is not None:
            try:
                filters.append(self.model.category_id == category_id)
            except KeyError: pass
        if region_id is not None:
            try:
                filters.append(self.model.region_id == region_id)
            except KeyError: pass
        if state_id is not None:
            try:
                filters.append(self.model.state_id == state_id)
            except KeyError: pass
        if country_id is not None:
            try:
                filters.append(self.model.country_id == country_id)
            except KeyError: pass

        count_query = select(func.count(self.model.id)).where(*filters)
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = select(self.model).where(*filters).offset(skip).limit(limit)
        result = await db.execute(data_query)
        items = result.scalars().all()

        return items, total_count

    async def get_places_count(self, db: AsyncSession) -> int:
        count_query = select(func.count(self.model.id))
        result = await db.execute(count_query)
        return result.scalar_one()

    # async def get_filtered(
    #     self,
    #     db: AsyncSession,
    #     name: Optional[str] = None,
    #     is_featured: Optional[bool] = None,
    #     category_id: Optional[UUID] = None,
    #     region_id: Optional[UUID] = None,
    #     state_id: Optional[UUID] = None,
    #     country_id: Optional[UUID] = None,
    #     skip: int = 0,
    #     limit: int = 100,
    # ) -> List[Place]:
    #     query = select(self.model)
    #
    #     if name is not None:
    #         query = query.where(self.model.name == name)
    #     if is_featured is not None:
    #         query = query.where(self.model.is_featured == is_featured)
    #     if category_id is not None:
    #         query = query.where(self.model.category_id == category_id)
    #     if region_id is not None:
    #         query = query.where(self.model.region_id == region_id)
    #     if state_id is not None:
    #         query = query.where(self.model.state_id == state_id)
    #     if country_id is not None:
    #         query = query.where(self.model.country_id == country_id)
    #
    #     query = query.offset(skip).limit(limit)
    #     result = await db.execute(query)
    #     return result.scalars().all()


place_crud = CRUDPlace(Place)
