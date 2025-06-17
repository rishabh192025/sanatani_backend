# app/models/festival.py (or event.py)
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base
# Assuming you have State, User, Category models
# from app.models.location_geo import State # Assuming State model path
# from app.models.user import User
# from app.models.category import Category # If festivals have categories

# If you create an EventType enum similar to PlaceType for content:
# from enum import Enum as PyEnum
# class EventType(PyEnum):
#     FESTIVAL = "FESTIVAL"
#     CULTURAL_EVENT = "CULTURAL_EVENT"
#     ...

class Festival(Base):
    __tablename__ = "festivals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True, unique=True) # Festival name should likely be unique
    alternate_names = Column(JSON, nullable=True) # e.g., {"tamil": "Karthigai Deepam", "sanskrit": "Kṛttikā Dīpaṃ"}
    description = Column(Text, nullable=True)
    
    # Significance and Observance
    significance = Column(Text, nullable=True) # Why is this festival celebrated?
    rituals_and_observances = Column(Text, nullable=True) # How is it celebrated? Common practices.
    deities_associated = Column(JSON, nullable=True) # List of primary deities, e.g., ["Ganesha", "Lakshmi"]
    
    start_date = Column(DateTime, nullable=True) # Approximate start for a given year
    end_date = Column(DateTime, nullable=True)   # Approximate end
    duration_days = Column(Integer, nullable=True, default=1)
    
    primary_tithi = Column(String(100), nullable=True) # e.g., "Chaitra Shukla Pratipada"
    primary_nakshatra = Column(String(100), nullable=True)
    hindu_month = Column(String(100), nullable=True) # e.g., "Kartika", "Chaitra"
    paksha = Column(String(50), nullable=True) # e.g., "Shukla", "Krishna"

    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=True) # Your requirement
    state = relationship("State") # Assuming one-way for now, or add back_populates to State
    
    images = Column(JSON, nullable=True) # List of image URLs
    is_major_festival = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True) # For soft delete or deactivating entries

    # Timestamps & User
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), nullable=False)
    #creator = relationship("User", viewonly=True) # Add back_populates to User model

    def __repr__(self):
        return f"<Festival(id={self.id}, name='{self.name}')>"
