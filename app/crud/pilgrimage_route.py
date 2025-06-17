from uuid import UUID
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Tuple

from app.models import PilgrimageRoute
from app.schemas import PilgrimageRouteCreate, PilgrimageRouteUpdate
from app.crud.base import CRUDBase
from app.utils.helpers import generate_slug


class CRUDPilgrimageRoute(CRUDBase[PilgrimageRoute, PilgrimageRouteCreate, PilgrimageRouteUpdate]):
    async def create_pilgrimage_route(self, db: AsyncSession, *, obj_in: PilgrimageRouteCreate, created_by: UUID) -> PilgrimageRoute:
        slug = await generate_slug(db, self.model, obj_in.name)
        # obj_in_data = jsonable_encoder(obj_in)        # converts date to str
        obj_in_data = obj_in.model_dump()       # preserves native Python types datetime.date, UUID, etc.
        obj_in_data["created_by"] = UUID(created_by) if isinstance(created_by, str) else created_by
        obj_in_data["slug"] = slug
        obj_in_data["difficulty_level"] = (
            obj_in.difficulty_level.value if obj_in.difficulty_level else None
        )
        obj_in_data["estimated_duration"] = (
            obj_in.estimated_duration.value if obj_in.estimated_duration else None
        )
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    # As of now allowing duplicate names, not using this
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[PilgrimageRoute]:
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalar_one_or_none()


    async def get_filtered_with_count(
        self,
        db: AsyncSession,
        name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PilgrimageRoute], int]:
        filters = []
        if name:
            filters.append(func.lower(self.model.name).ilike(f"%{name.lower()}%"))

        count_query = select(func.count(self.model.id)).where(*filters)
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = select(self.model).where(*filters).offset(skip).limit(limit)
        result = await db.execute(data_query)
        items = result.scalars().all()

        return items, total_count


    # async def get_filtered(
    #         self,
    #         db: AsyncSession,
    #         name: Optional[str] = None,
    #         skip: int = 0,
    #         limit: int = 100,
    # ) -> List[PilgrimageRoute]:
    #     query = select(self.model)
    #
    #     if name is not None:
    #         # query = query.where(self.model.name == name)
    #         query = query.where(func.lower(self.model.name).ilike(f"%{name.lower()}%"))       # added ILIKE if asked to remove uncomment above one
    #     query = query.offset(skip).limit(limit)
    #     result = await db.execute(query)
    #     return result.scalars().all()


pilgrimage_route_crud = CRUDPilgrimageRoute(PilgrimageRoute)

