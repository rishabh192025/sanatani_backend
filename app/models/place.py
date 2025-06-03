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


# Sacred Places & Geography
class SacredPlace(Base):
    __tablename__ = "sacred_places"

    # Place Basic Info
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_name = Column(String(200), nullable=False, index=True)
    alternate_names = Column(JSON, nullable=True)  # Array of alternative names, not needed now
    categories = Column(Enum(PlaceType), nullable=False, index=True) # changed this to match UI

    # Location Details
    region = Column(String(100))  # added this to match UI
    address = Column(Text, nullable=True)   # not needed now
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), nullable=True)     # not needed now
    place_description = Column(Text, nullable=True)  # place description

    # Geographic Coordinates
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)  # meters above sea level # not needed now
    location_description = Column(Text, nullable=True)  # Location Description

    # Detailed Information
    historical_background = Column(Text, nullable=True)     # changed this to match UI
    religious_importance = Column(Text, nullable=True)      # changed this to match UI
    legends_stories = Column(Text, nullable=True)       # not needed now

    # Temple/Place Specific     # not needed now
    deity_names = Column(JSON, nullable=True)  # Primary deities
    architectural_style = Column(String(100), nullable=True)
    built_year = Column(Integer, nullable=True)
    built_century = Column(String(50), nullable=True)  # "12th century BCE"
    dynasty_period = Column(String(100), nullable=True)

    # Visitor Information       # not needed now
    visiting_hours = Column(JSON, nullable=True)  # Structured schedule
    entry_fee = Column(JSON, nullable=True)  # Different categories
    dress_code = Column(Text, nullable=True)
    special_rituals = Column(JSON, nullable=True)
    festivals_celebrated = Column(JSON, nullable=True)

    # Media
    images = Column(JSON, nullable=True)  # Array of image URLs, both cover and gallery
    videos = Column(JSON, nullable=True)  # Array of video URLs     # not needed now
    virtual_tour_url = Column(String(500), nullable=True)       # not needed now

    # Status & Verification # not needed now
    verification_status = Column(String(50), default="pending")  # verified, pending, disputed
    is_active = Column(Boolean, default=True)
    accessibility_info = Column(JSON, nullable=True)

    # Engagement    # not needed now
    visit_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # # Relationships
    # pilgrimage_routes = relationship("PilgrimageRoutePlace", back_populates="place")

    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_place_country_type', 'country', 'categories'),
    )
