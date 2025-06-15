# app/models/user.py
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

# Enums
class UserRole(PyEnum): # Keep Python Enum for direct use
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    USER = "USER"
    GUEST = "GUEST"

class LanguageCode(PyEnum): # Keep Python Enum
    EN = "EN"
    HI = "HI"
    SA = "AS"
    BN = "BN"
    TA = "TA"
    TE = "TE"
    MR = "MR"
    GU = "GU"
    KA = "KA"
    ML = "ML"
    OR = "OR"
    PA = "PA"
    UR = "UR"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    
    spiritual_name = Column(String(150), nullable=True)
    guru_lineage = Column(String(200), nullable=True)
    meditation_level = Column(String(50), nullable=True)
    preferred_practices = Column(JSON, nullable=True)
    
    country = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    preferred_language = Column(String(50), default=LanguageCode.EN.value)
    
    role = Column(String(50), default=UserRole.USER.value, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    subscription_tier = Column(String(50), default="free")
    subscription_starts_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships - Add other models as they are created
    # created_content = relationship("Content", back_populates="author", foreign_keys="Content.author_id") # Example
    # user_progress = relationship("UserProgress", back_populates="user")
    # bookmarks = relationship("UserBookmark", back_populates="user")
    # reviews = relationship("ContentReview", back_populates="user")
    places = relationship("Place", back_populates="user")
    temples = relationship("Temple", back_populates="user")

    # For self-referential created_by
    # creator = relationship("User", remote_side=[id], backref="created_users") # If needed

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"