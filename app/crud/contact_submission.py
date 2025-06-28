# app/crud/contact_submission.py

from typing import List, Optional, Tuple
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.contact_submission import ContactSubmission, ContactStatus
from app.schemas.contact_submission import ContactSubmissionCreate, ContactSubmissionUpdateAdmin

class CRUDContactSubmission(CRUDBase[ContactSubmission, ContactSubmissionCreate, ContactSubmissionUpdateAdmin]):
    
    async def create_submission(self, db: AsyncSession, *, obj_in: ContactSubmissionCreate) -> ContactSubmission:
        # The base `create` method works perfectly for this simple case.
        # We can call it directly.
        return await super().create(db=db, obj_in=obj_in)

    async def get_submissions_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[ContactStatus] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[ContactSubmission], int]:
        
        # Base query for filtering
        filters = []
        if status_filter:
            filters.append(self.model.status == status_filter.value)
        
        if search_query:
            term = f"%{search_query}%"
            filters.append(
                or_(
                    self.model.email.ilike(term),
                    self.model.subject.ilike(term),
                    self.model.name.ilike(term)
                )
            )

        # Count query
        count_query = select(func.count(self.model.id)).select_from(self.model)
        if filters:
            count_query = count_query.where(*filters)
        
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Data query
        data_query = select(self.model).order_by(self.model.created_at.desc())
        if filters:
            data_query = data_query.where(*filters)
        
        data_query = data_query.options(selectinload(self.model.resolved_by)).offset(skip).limit(limit)
        
        data_result = await db.execute(data_query)
        items = data_result.scalars().all()
        
        return items, total_count

    async def update_submission_status(
        self,
        db: AsyncSession,
        *,
        db_obj: ContactSubmission,
        obj_in: ContactSubmissionUpdateAdmin,
        resolver_id: Optional[PyUUID] = None
    ) -> ContactSubmission:
        
        update_data = obj_in.model_dump(exclude_unset=True)

        # Convert Enum to string
        if "status" in update_data and isinstance(update_data["status"], ContactStatus):
            update_data["status"] = update_data["status"].value

        if update_data.get("status") == ContactStatus.RESOLVED.value and resolver_id:
            db_obj.resolved_by_id = resolver_id

        return await super().update(db=db, db_obj=db_obj, obj_in=update_data)



contact_submission_crud = CRUDContactSubmission(ContactSubmission)