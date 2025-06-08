# app/schemas/book_chapter.py
from pydantic import BaseModel, Field, HttpUrl, model_validator
from typing import Optional, List, Any
from pydantic import ValidationInfo
from app.models.content import BookChapter  # Import your SQLAlchemy model
from uuid import UUID
from datetime import datetime
from app.schemas.book_section import BookSectionResponse # Import section schema

class BookChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    #chapter_number: int = Field(..., gt=0)
    description: Optional[str] = None

class BookChapterCreate(BookChapterBase):
    pass

class BookChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None # New field

class BookChapterResponseWithoutSections(BookChapterBase):
    id: UUID
    book_id: UUID
    chapter_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookChapterResponse(BookChapterResponseWithoutSections):
    sections: Optional[List[BookSectionResponse]] = None # Added sections

    class Config:
        from_attributes = True
    
    #This validator will run after initial population from attributes
    @model_validator(mode='before') # 'before' might be better here
    @classmethod
    def handle_sections_loading(cls, data: Any, info: ValidationInfo) -> Any:
        # 'data' will be the SQLAlchemy model instance when from_attributes=True
        if isinstance(data, BookChapter):
            # Check if 'sections' relationship is loaded
            # The 'load_sections' flag was used in the CRUD to *decide* to load.
            # If it wasn't loaded, data.sections is an InstrumentedAttribute.
            # Pydantic should ideally treat Optional fields as None if the attribute
            # is an unloaded InstrumentedAttribute.
            
            # A simpler check for this specific case: if sections is in the context, use it.
            # This context would be set by the API route if needed.
            # if info.context and "loaded_sections" in info.context:
            #    # This is getting too complex. Let's simplify.
            #    # The core issue is Pydantic trying to access the unloaded relationship.
            #    # By making `sections: Optional[List[BookSectionResponse]] = None`,
            #    # Pydantic *should* be fine if the `chapter_model.sections` is an empty list
            #    # (when loaded with selectinload and no sections exist) OR if it's None.
            #    # The problem is the InstrumentedAttribute state.
            pass
        return data