# app/crud/teaching.py
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_

from app.crud.base import CRUDBase
from app.models.content import Content, ContentSubType, ContentType as ModelContentTypeEnum, ContentStatus, LanguageCode as ModelLanguageCode
from app.schemas.teaching import TeachingCreate, TeachingUpdate # Use specific Teaching schemas
from app.utils.helpers import generate_slug

class CRUDTeaching(CRUDBase[Content, TeachingCreate, TeachingUpdate]): # Typed with Teaching schemas

    async def create_teaching(
        self, db: AsyncSession, *, obj_in: TeachingCreate, author_id: PyUUID
    ) -> Content:
        slug = await generate_slug(db, self.model, obj_in.title)
        
        # obj_in.format (ARTICLE, AUDIO, VIDEO) determines the Content.content_type
        actual_content_type_value = obj_in.content_type.value 

        # Exclude 'format' as it's used to determine content_type.
        # Other fields like content_body, file_url, duration are directly from TeachingCreate.
        teaching_data_dict = obj_in.model_dump(exclude={"category_id", "format", "content_type"})
        db_obj = Content(
            **teaching_data_dict,
            content_type=actual_content_type_value,
            sub_type=ContentSubType.TEACHING.value,
            author_id=author_id,
            slug=slug
        )

        if obj_in.category_id:
            try:
                db_obj.category_id = PyUUID(obj_in.category_id)
            except ValueError: pass

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_teaching(self, db: AsyncSession, teaching_id: PyUUID) -> Optional[Content]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.id == teaching_id)
            .filter(self.model.sub_type == ContentSubType.TEACHING.value)
        )
        return result.scalar_one_or_none()

    async def get_teaching_by_slug(self, db: AsyncSession, slug: str) -> Optional[Content]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.slug == slug)
            .filter(self.model.sub_type == ContentSubType.TEACHING.value)
        )
        return result.scalar_one_or_none()

    async def get_teachings_list_and_count(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 10,
        content_type_str: Optional[str] = None, # Client sends "ARTICLE", "AUDIO", "VIDEO"
        status_str: Optional[str] = None,
        category_id_str: Optional[str] = None,
        language_str: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Content], int]:
        
        filters = [self.model.sub_type == ContentSubType.TEACHING.value]
        print(content_type_str, status_str, category_id_str, language_str, search_query)
        if content_type_str:
            try:
                filters.append(self.model.content_type == ModelContentTypeEnum[content_type_str.upper()].value)
            except KeyError: pass 
        if status_str:
            try: filters.append(self.model.status == ContentStatus[status_str.upper()].value)
            except KeyError: pass
        if category_id_str:
            try: filters.append(self.model.category_id == PyUUID(category_id_str))
            except ValueError: pass
        if language_str:
            try: filters.append(self.model.language == ModelLanguageCode[language_str.upper()].value)
            except KeyError: pass
        if search_query:
            term = f"%{search_query}%"
            filters.append(or_(self.model.title.ilike(term), self.model.description.ilike(term)))
            
        print(f"Filters applied: {filters}")
        count_query = select(func.count(self.model.id)).select_from(self.model).where(*filters)
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = select(self.model).where(*filters).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        items_result = await db.execute(data_query)
        items = items_result.scalars().all()
        print(f"Retrieved {len(items)} items with total count {total_count} from the database.")
        return items, total_count

    async def update_teaching(
        self, db: AsyncSession, *, db_obj: Content, obj_in: TeachingUpdate
    ) -> Content:
        if db_obj.sub_type != ContentSubType.TEACHING.value:
            raise ValueError("Cannot update non-teaching content using teaching update logic.")
        # Note: TeachingUpdate schema doesn't allow changing format (content_type).
        # If it did, you'd need logic here to handle that.
        return await super().update(db=db, db_obj=db_obj, obj_in=obj_in)

teaching_crud = CRUDTeaching(Content)