# app/models/user_bookmark.py
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Enum as SQLAlchemyEnum, JSON # Renamed Enum to SQLAlchemyEnum to avoid clash
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base # Corrected import

class UserBookmark(Base):
    __tablename__ = "user_bookmarks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    # bookmark_type is good if you plan to bookmark other things like places/events with a different FK.
    # For now, if it's only for content, it's optional but doesn't hurt.
    bookmark_type = Column(String(50), default="content")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="bookmarks") # Add back_populates="bookmarks" to User.bookmarks
    content = relationship("Content") # No back_populates needed on Content unless you want user_bookmarks list there.

    __table_args__ = (
        UniqueConstraint('user_id', 'content_id', name='unique_user_content_bookmark'),
    )