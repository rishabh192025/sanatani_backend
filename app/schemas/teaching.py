# app/schemas/teaching.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.content import LanguageCode, ContentStatus, ContentType as ModelContentTypeEnum 

class TeachingDetails(BaseModel):
    about: Optional[str] = None
    key_concepts: Optional[List[str]] = Field(None, description="A list of key concepts discussed.")
    benefits: Optional[List[str]] = Field(None, description="A list of benefits for the practitioner.")

# Base for common teaching fields
class TeachingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    language: str = LanguageCode.EN.value
    tags: Optional[List[str]] = Field(None, max_items=20)
    cover_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    details: Optional[TeachingDetails] = None

class TeachingCreate(TeachingBase):
    content_type: ModelContentTypeEnum = ModelContentTypeEnum.ARTICLE 
    # Client explicitly sends ARTICLE, AUDIO, or VIDEO
    
    # Conditional fields based on format
    file_url: Optional[str] = None     # For AUDIO, VIDEO (or from upload)
    duration: Optional[int] = Field(None, ge=0) # For AUDIO, VIDEO

    category_id: Optional[str] = None
    author_name: Optional[str] = Field(None, max_length=200) 
    status: Optional[str] = ContentStatus.PUBLISHED.value
    featured: Optional[bool] = False
    premium_content: bool = False
    # sub_type will be set by CRUDTeaching to TEACHING

class TeachingUpdate(TeachingBase): # Specific fields for updating a teaching
    
    # Format is generally not updatable once set (e.g., can't change an article to a video easily)
    # If you need to update these, add them:
    file_url: Optional[str] = None     
    duration: Optional[int] = Field(None, ge=0)

    category_id: Optional[str] = None
    author_name: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = ContentStatus.PUBLISHED.value
    featured: Optional[bool] = None
    premium_content: Optional[bool] = None

class TeachingResponse(TeachingBase): # Inherits fields from TeachingBase
    id: UUID
    slug: str
    content_type: str # ARTICLE, AUDIO, or VIDEO (reflects the format)
    #sub_type: str    # Will be TEACHING
    
    file_url: Optional[str] = None     
    duration: Optional[int] = None     

    author_id: Optional[UUID] = None
    author_name: Optional[str] = None
    category_id: Optional[UUID] = None # Or str
    status: str
    published_at: Optional[datetime] = None
    featured: bool
    premium_content: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True