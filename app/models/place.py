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


# Place
class Place(Base):
    __tablename__ = "place"

    # Basic Info
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region = Column(String(100))
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Place Information
    name = Column(String(200), nullable=False, index=True)
    place_description = Column(Text, nullable=True)  # place description

    # Categories
    category = Column(String(200), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    is_featured = Column(Boolean, default=False)

    # Detailed Information
    religious_importance = Column(Text, nullable=True)
    historical_background = Column(Text, nullable=True)

    # Location
    location_description = Column(Text, nullable=True)  # Location Description
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Media
    cover_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, nullable=True)  # Array of image URLs

    # Status
    is_active = Column(Boolean, default=True)       # soft delete flag

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # # Relationships
    # pilgrimage_routes = relationship("PilgrimageRoutePlace", back_populates="place")

    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_place_region_type', 'region', 'category'),
    )
