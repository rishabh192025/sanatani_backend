# app/crud/festival.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func, or_ # Import or_ for search
from typing import Optional, List, Tuple
from uuid import UUID as PyUUID
from datetime import timezone
from app.models.festival import Festival # Your Festival model
from app.schemas.festival import FestivalCreate, FestivalUpdate
from app.crud.base import CRUDBase

class CRUDFestival(CRUDBase[Festival, FestivalCreate, FestivalUpdate]):
    
    async def create_festival(
        self, db: AsyncSession, *, obj_in: FestivalCreate, created_by_id: PyUUID
    ) -> Festival:
        print(f"DEBUG: Attempting to create festival with name: '{obj_in.name}'")
        existing_festival = await self.get_by_name(db, name=obj_in.name)
        
        # VERY IMPORTANT: Print immediately after the query and before the condition
        print(f"DEBUG: Result of get_by_name for '{obj_in.name}': {existing_festival}, Type: {type(existing_festival)}")
        
        if existing_festival:
            print(f"DEBUG: Condition 'if existing_festival' is TRUE for name '{obj_in.name}'. Raising ValueError.")
            raise ValueError(f"A festival with the name '{obj_in.name}' already exists.")
        else:
            print(f"DEBUG: Condition 'if existing_festival' is FALSE for name '{obj_in.name}'. Proceeding to create.")

        # Prepare data for the model, converting HttpUrl to str
        festival_data_for_db = obj_in.model_dump() # Get all data from Pydantic model

        if festival_data_for_db.get("images") is not None:
            # Convert each HttpUrl in the list to its string representation
            festival_data_for_db["images"] = [str(url) for url in festival_data_for_db["images"]]
        if "start_date" in festival_data_for_db and festival_data_for_db["start_date"] is not None:
            dt = festival_data_for_db["start_date"]
            # Check if it's timezone-aware
            if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
                # Convert to UTC and then remove timezone info
                festival_data_for_db["start_date"] = dt.astimezone(timezone.utc).replace(tzinfo=None)

        if "end_date" in festival_data_for_db and festival_data_for_db["end_date"] is not None:
            dt = festival_data_for_db["end_date"]
            # Check if it's timezone-aware
            if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
                # Convert to UTC and then remove timezone info
                festival_data_for_db["end_date"] = dt.astimezone(timezone.utc).replace(tzinfo=None)
        # Ensure 'created_by_id' is not accidentally overwritten if it's part of FestivalCreate schema
        # and also passed as a separate argument. It's safer to add it explicitly or remove from spread.
        # For simplicity, if 'created_by_id' is NOT in FestivalCreate:
        db_obj = self.model(
            **festival_data_for_db,  # <-- USE THE MODIFIED DICTIONARY HERE
            created_by_id=created_by_id
        )
        # If 'created_by_id' COULD be in FestivalCreate (e.g. for an admin setting it), 
        # but you want to prioritize the passed 'created_by_id':
        # festival_data_for_db.pop('created_by_id', None) # Remove if present to avoid duplicate kwarg
        # db_obj = self.model(**festival_data_for_db, created_by_id=created_by_id)


        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Festival]:
        result = await db.execute(select(self.model).filter(self.model.name == name)).filter(self.model.is_deleted.is_(False))
        return result.scalar_one_or_none()

    async def get_festivals_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        state_id: Optional[PyUUID] = None,
        # category_id: Optional[PyUUID] = None,
        is_major: Optional[bool] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Festival], int]:
        
        count_query = select(func.count(self.model.id)).select_from(self.model).where(self.model.is_deleted.is_(False))
        data_query = select(self.model).where(self.model.is_deleted.is_(False)) # .options(selectinload(self.model.state)) # Eager load state

        filters = []
        if state_id is not None:
            filters.append(self.model.state_id == state_id)
        # if category_id is not None:
        #     filters.append(self.model.category_id == category_id)
        if is_major is not None:
            filters.append(self.model.is_major_festival == is_major)
        if search_query:
            term = f"%{search_query}%"
            filters.append(
                or_(
                    self.model.name.ilike(term),
                    self.model.description.ilike(term),
                    # Add other searchable fields if needed
                )
            )

        if filters:
            count_query = count_query.where(*filters)
            data_query = data_query.where(*filters)
        
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        data_query = data_query.order_by(self.model.name).offset(skip).limit(limit)
        items_result = await db.execute(data_query)
        items = items_result.scalars().all()
        
        return items, total_count

    async def get_festivals_count(
        self, db: AsyncSession,
        *, 
        state_id: Optional[PyUUID] = None, 
        is_major: Optional[bool] = None
    ) -> int:
        count_query = select(func.count(self.model.id)).select_from(self.model).where(self.model.is_deleted.is_(False))
        filters = []
        if state_id is not None:
            filters.append(self.model.state_id == state_id)
        if is_major is not None:
            filters.append(self.model.is_major_festival == is_major)
        if filters:
            count_query = count_query.where(*filters)
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        return total_count

    async def update_festival(
        self, db: AsyncSession, *, db_obj: Festival, obj_in: FestivalUpdate
    ) -> Festival:
        if obj_in.name and obj_in.name != db_obj.name:
            existing_festival = await self.get_by_name(db, name=obj_in.name)
            if existing_festival and existing_festival.id != db_obj.id:
                raise ValueError(f"A festival with the name '{obj_in.name}' already exists.")
        
        # Get data from Pydantic model, excluding unset fields
        update_data_for_db = obj_in.model_dump(exclude_unset=True) 

        if "images" in update_data_for_db and update_data_for_db["images"] is not None:
            # Convert HttpUrl objects to strings if present in the update
            update_data_for_db["images"] = [str(url) for url in update_data_for_db["images"]]
        
        if "start_date" in update_data_for_db and update_data_for_db["start_date"] is not None:
            dt = update_data_for_db["start_date"]
            if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
                update_data_for_db["start_date"] = dt.astimezone(timezone.utc).replace(tzinfo=None)

        if "end_date" in update_data_for_db and update_data_for_db["end_date"] is not None:
            dt = update_data_for_db["end_date"]
            if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
                update_data_for_db["end_date"] = dt.astimezone(timezone.utc).replace(tzinfo=None)
        # Apply updates from the modified dictionary
        for field, value in update_data_for_db.items():
            setattr(db_obj, field, value)
        
        # db.add(db_obj) # Not strictly necessary if db_obj is already in session and modified
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

festival_crud = CRUDFestival(Festival)