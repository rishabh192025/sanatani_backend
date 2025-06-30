# app/models/chat_with_guruji.py
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


class ChatWithGuruji(Base):
    __tablename__ = "chat_with_guruji"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(String(100), nullable=False)
    messages = Column(JSON, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    source =  Column(String(100), nullable=True)                   # AI model

    # Status
    is_active = Column(Boolean, default=True)       # soft delete flag
    title = Column(String(300), nullable=True)  # Optional title for the chat

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chats_with_guruji")

    # __table_args__ = (
    #     Index('idx_chat_with_guruji_chat_id', 'chat_id'),
    # )