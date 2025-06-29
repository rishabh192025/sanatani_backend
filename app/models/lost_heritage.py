# app/models/lost_heritage.py
from app.database import Base
from enum import Enum

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
    content_type =  Column(String(100), nullable=False)

    # Content
    article_content = Column(Text, nullable=True)
    video_url = Column(String(1000), nullable=True)
    gallery_images = Column(JSON, nullable=True)       # list of images

    # Metadata
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    location = Column(String(1000), nullable=True, index=True)
    time_period = Column(String(200), nullable=True)       # eg. 5th Century BCE
    historical_significance = Column(Text, nullable=True)
    current_status = Column(String(1000), nullable=True)          # partially preserved, under restoration
    author = Column(String(200), nullable=True)          # name contributor of content
    tags = Column(JSON, nullable=True)       # list of tags

    # Images
    thumbnail_image = Column(JSON, nullable=True)       # list of images

    # Status
    is_active = Column(Boolean, default=True)       # soft delete flag
    is_featured = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)       # if false means DRAFT

    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="lost_heritages")
    user = relationship("User", back_populates="lost_heritages")

    __table_args__ = (
        Index('idx_lost_heritage_location', 'location'),
    )