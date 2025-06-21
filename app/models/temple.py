# app/models/temple.py
from app.database import Base

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum, JSON, LargeBinary, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Temple(Base):
    __tablename__ = "temples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"), nullable=False)
    name = Column(String(200), nullable=False)
    main_deity = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    visiting_hours = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    history = Column(Text, nullable=True)
    architecture = Column(Text, nullable=True)
    cover_image = Column(JSON, nullable=True)
    is_featured = Column(Boolean, nullable=True)
    is_active = Column(Boolean, default=True)               # soft delete flag
    visit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="temples")
    place = relationship("Place", back_populates="temples")

    # __table_args__ = (
    #     Index('idx_temple_name', 'name'),
    # )