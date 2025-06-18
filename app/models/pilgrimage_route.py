# app/models/pilgrimage_route.py
from app.database import Base

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum, JSON, LargeBinary, UniqueConstraint, Index, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID


class PilgrimageRoute(Base):
    __tablename__ = "pilgrimage_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(Text, nullable=True)              # call the create slug fn and store
    spiritual_significance = Column(Text, nullable=True)

    # category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)     # not using as of now
    difficulty_level = Column(String(200), nullable=True)
    estimated_duration = Column(String(200), nullable=True)
    best_season_start = Column(Date, nullable=False)            # e.g., 1900-03-21
    best_season_end = Column(Date, nullable=False)              # e.g., 1900-06-20

    itinerary = Column(Text, nullable=True)
    route_path = Column(JSON, nullable=True)        # Route Stops, for displaying in UI admin will calculate the len of arr, array of places id call list all places api

    cover_image = Column(String(500), nullable=True)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)               # soft delete flag
    view_count = Column(Integer, default=0)              # view_count of that route

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    # category = relationship("Category", back_populates="categories")
    user = relationship("User", back_populates="pilgrimage_routes")