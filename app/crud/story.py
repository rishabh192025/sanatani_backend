# app/crud/story.py
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_

from app.crud.base import CRUDBase
from app.models.content import Content, ContentSubType, ContentType as ModelContentTypeEnum, ContentStatus, LanguageCode as ModelLanguageCode
from app.schemas.story import StoryCreate, StoryUpdate # Use specific Story schemas
from app.utils.helpers import generate_slug

class CRUDStory(CRUDBase[Content, StoryCreate, StoryUpdate]): # Typed with Story schemas
    
    async def create_story(
        self, db: AsyncSession, *, obj_in: StoryCreate, author_id: PyUUID
    ) -> Content:
        slug = await generate_slug(db, self.model, obj_in.title)
        
        # model_dump from StoryCreate will include title, description, language, tags etc.
        story_data_dict = obj_in.model_dump(exclude={"category_id"}) 

        db_obj = Content(
            **story_data_dict, # Spread fields from StoryCreate
            content_type=ModelContentTypeEnum.ARTICLE.value, # Stories are ARTICLE type
            sub_type=ContentSubType.STORY.value,       # Specifically a STORY
            author_id=author_id,
            slug=slug,
            # status, featured, premium_content, author_name are already in story_data_dict from StoryCreate
        )

        if obj_in.category_id:
            try:
                db_obj.category_id = PyUUID(obj_in.category_id)
            except ValueError: pass 

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_story(self, db: AsyncSession, story_id: PyUUID) -> Optional[Content]:
        result = await db.execute(
            select(self.model) # self.model is Content
            .filter(self.model.id == story_id)
            .filter(self.model.sub_type == ContentSubType.STORY.value)
            # Optionally, also filter by content_type if stories can ONLY be articles
            # .filter(self.model.content_type == ModelContentTypeEnum.ARTICLE.value) 
        )
        return result.scalar_one_or_none()

    async def get_story_by_slug(self, db: AsyncSession, slug: str) -> Optional[Content]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.slug == slug)
            .filter(self.model.sub_type == ContentSubType.STORY.value)
            # .filter(self.model.content_type == ModelContentTypeEnum.ARTICLE.value)
        )
        return result.scalar_one_or_none()

    async def get_stories_list_and_count(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 10,
        status_str: Optional[str] = None, # Allow filtering by any status
        category_id_str: Optional[str] = None,
        language_str: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Content], int]:
        
        filters = [
            self.model.sub_type == ContentSubType.STORY.value,
            # self.model.content_type == ModelContentTypeEnum.ARTICLE.value # If stories are always articles
        ]
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


        count_query = select(func.count(self.model.id)).select_from(self.model).where(*filters)
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        data_query = select(self.model).where(*filters).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        items_result = await db.execute(data_query)
        items = items_result.scalars().all()
        
        return items, total_count

    # update method can be inherited from CRUDBase, but ensure ContentUpdate schema is used
    # or create a specific update_story method.
    async def update_story(
        self, db: AsyncSession, *, db_obj: Content, obj_in: StoryUpdate
    ) -> Content:
        # Ensure this operation is only on an actual story
        if db_obj.sub_type != ContentSubType.STORY.value: # or db_obj.sub_type_enum != ContentSubType.STORY
            raise ValueError("Cannot update non-story content using story update logic.")
        # obj_in is StoryUpdate, so fields are specific to story
        return await super().update(db=db, db_obj=db_obj, obj_in=obj_in)

story_crud = CRUDStory(Content)