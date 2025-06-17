# app/models/category.py
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey,
    Enum as SQLAlchemyEnum # Import SQLAlchemyEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum # Keep Python Enum for application use

from app.database import Base

# New Enum for Category Type
class CategoryScopeType(PyEnum): # Or CategoryContextType, CategoryAppliesToType
    GENERAL = "GENERAL"         # Applicable to any content type
    BOOK = "BOOK"             # Specifically for books
    STORY = "STORY"           # Specifically for stories
    TEACHING = "TEACHING"       # Specifically for teachings
    ARTICLE = "ARTICLE"         # General articles if different from teachings/stories
    AUDIO = "AUDIO"             # For audio content categories
    VIDEO = "VIDEO"             # For video content categories
    SACRED_PLACE = "SACRED_PLACE" # If categories apply to places
    EVENT = "EVENT"             # If categories apply to calendar events
    # Add more as your application grows and needs more specific category groupings

class Category(Base):
    __tablename__ = "categories"
    # __table_args__ = {'extend_existing': True} # Only needed if redefining in same session, usually not for models

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    color_code = Column(String(7), nullable=True) # e.g., #RRGGBB
    
    # New field to define the scope of the category
    type = Column(String(50), default=CategoryScopeType.BOOK.value, nullable=False, index=True)
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False) # Usually non-nullable
    is_featured = Column(Boolean, default=False, index=True) # Added for homepage/featured sections
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    parent = relationship("Category", remote_side=[id], back_populates="children")
    places = relationship("Place", back_populates="category")
    # pilgrimage_routes = relationship("PilgrimageRoute", back_populates="category")
    # content = relationship("Content", back_populates="category") # Defined in Content model via backref
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    
    # Relationship to Content (Content model has category_id FK)
    # content_items = relationship("Content", back_populates="category") # This is defined via backref on Content.category

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type if self.type else None}')>"