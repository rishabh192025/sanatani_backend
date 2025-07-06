# app/models/place.py
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


class Place(Base):
    __tablename__ = "places"

    # Basic Info
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"))
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"))
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"))
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"))

    # Place Information
    name = Column(String(200), nullable=False, index=True)
    place_description = Column(Text, nullable=True)  # place description

    # Categories
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
    is_deleted = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    country = relationship("Country", back_populates="places")
    region = relationship("Region", back_populates="places")
    state = relationship("State", back_populates="places")
    city = relationship("City", back_populates="places")
    category = relationship("Category", back_populates="places")
    user = relationship("User", back_populates="places")

    # pilgrimage_routes = relationship("PilgrimageRoutePlace", back_populates="place")
    temples = relationship("Temple", back_populates="place")

    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
    )