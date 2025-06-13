# app/models/lost_heritage.py
from app.database import Base
from enum import Enum
from app.schemas.place import PlaceType

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum, JSON, LargeBinary, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID


class LostHeritage(Base):
    __tablename__ = "lost_heritage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    content_type =  Column(String(100), nullable=False)     # TODO: ask sir as in the UI as of now only three content types are there like Article Documentary Gallery, so storing as string only, dont get confused with category, this shows only type of content (do I need to use Enum here for validation)?/ add as per me

    # Content
    article_content = Column(Text, nullable=True)       # TODO: ask sir that after selecting content if we select article then it will store text and as per me it has no word restriction but for Doc it has URL(checked comma separated multiple urls doesnt work) which will work if stored in text as only 1 url but for Gallery there is a list of images so have to store JSON here will text work in json or have to create one column which will be empty if any of 3 is selected which is fine as per me
    video_url = Column(String(1000), nullable=True)
    gallery_images = Column(JSON, nullable=True)       # list of images

    # Metadata
    category = Column(String(200), nullable=False, index=True)      # create ENUM for validation like places, but everytime a new category is added have to update ENUM
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    location = Column(String(1000), nullable=True, index=True)          # add index in this?
    time_period = Column(String(200), nullable=True)       # eg. 5th Century BCE
    historical_significance = Column(Text, nullable=True)
    current_status = Column(String(1000), nullable=True)          # partially preserved, under restoration
    author = Column(String(200), nullable=True)          # name of author/ contributor of content?? or heritage? ig content
    tags = Column(JSON, nullable=True)       # list of tags as per me

    # Images
    thumbnail_image = Column(JSON, nullable=True)       # list of images

    # Status
    is_active = Column(Boolean, default=True)       # soft delete flag
    is_featured = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)       # TODO: ask sir that in view all of admin side there are two types of status Draft and published so, this only column will work if there are two else have to create ENUM as of now if false means DRAFT

    # view_count = .... # TODO: view_count on user has there is a view count how to implement that ask sir, store and whenever someone calls that get place by id then create a api and call to update viewcount of that particular lost_heritage_id
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        Index('idx_location', 'location'),
        Index('idx_category', 'category'),
    )