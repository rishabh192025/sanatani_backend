# app/models/contact_submission.py

from sqlalchemy import Column, String, Text, DateTime, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.user import User  # For the relationship

class ContactStatus(PyEnum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"

class ContactSubmission(Base):
    __tablename__ = "contact_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Admin-facing fields
    status = Column(
        String(50), 
        default=ContactStatus.NEW.value, 
        nullable=False, 
        index=True
    )
    admin_notes = Column(Text, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to the user who resolved it
    resolved_by = relationship("User")

    def __repr__(self):
        return f"<ContactSubmission(id={self.id}, email='{self.email}', status='{self.status}')>"