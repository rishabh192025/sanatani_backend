# app/models/content.py
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Enum as SQLAlchemyEnum, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base # Corrected import
from app.models.user import User # Import User for relationship
from app.models.user import LanguageCode

# Enums
class ContentStatus(PyEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    PENDING_REVIEW = "PENDING_REVIEW"


class ContentType(PyEnum): # Renamed from ContentEntityType for brevity
    BOOK = "BOOK"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    ARTICLE = "ARTICLE"
    PODCAST_SERIES = "PODCAST_SERIES" # A series, episodes would be chapters/sections or related content
    DIGITAL_TEXT = "DIGITAL_TEXT" # For scriptures, manuscripts if distinct from book/article
    # Add more as needed

class ContentSubType(PyEnum): # New Enum for more specific classification
    BOOK = "BOOK"
    GENERAL = "GENERAL" # Default
    STORY = "STORY"
    TEACHING = "TEACHING"
    SCRIPTURE = "SCRIPTURE"
    MANTRA = "MANTRA"
    GUIDED_MEDITATION = "GUIDED_MEDITATION"
    PODCAST_EPISODE = "PODCAST_EPISODE" # If an episode is a top-level content item
    # Add others as needed

class BookType(PyEnum):
    TEXT = "TEXT"  # For e-books, PDFs, etc.
    PDF = "PDF"  # For audiobooks
    AUDIO = "AUDIO"  # For audiobooks, podcasts, etc.


class Content(Base):
    __tablename__ = "content"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False, index=True)
    slug = Column(String(350), unique=True, nullable=False, index=True)
    subtitle = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    content_type = Column(String(50), nullable=False, index=True)
    sub_type = Column(String(50), default=ContentSubType.GENERAL.value, nullable=True, index=True)
    status = Column(String(50), default=ContentStatus.DRAFT.value, nullable=False)

    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, nullable=True)
    language = Column(String(50), default=LanguageCode.EN, nullable=False)
    
    cover_image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    author_name = Column(String(200), nullable=True)
    translator = Column(String(200), nullable=True)
    narrator = Column(String(200), nullable=True)
    
    published_at = Column(DateTime, nullable=True)
    featured = Column(Boolean, default=False)
    premium_content = Column(Boolean, default=False)
    
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)
    
    meta_title = Column(String(160), nullable=True)
    meta_description = Column(String(320), nullable=True)
    keywords = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    author = relationship("User", backref="created_content") # Simpler backref
    category = relationship("Category", backref="content_items") # Ensure Category model exists
    chapters = relationship("ContentChapter", back_populates="content", cascade="all, delete-orphan", order_by="ContentChapter.chapter_number")
    # reviews = relationship("ContentReview", back_populates="content")
    # user_progress = relationship("UserProgress", back_populates="content")
    translations = relationship("ContentTranslation", back_populates="original_content")
    collection_associations = relationship("CollectionItem", back_populates="content_item")

    # Enum property accessors
    @property
    def content_type_enum(self) -> ContentType:
        return ContentType(self.content_type)

    @content_type_enum.setter
    def content_type_enum(self, value: ContentType):
        self.content_type = value.value

    @property
    def sub_type_enum(self) -> ContentSubType:
        return ContentSubType(self.sub_type)

    @sub_type_enum.setter
    def sub_type_enum(self, value: ContentSubType):
        self.sub_type = value.value

    @property
    def status_enum(self) -> ContentStatus:
        return ContentStatus(self.status)

    @status_enum.setter
    def status_enum(self, value: ContentStatus):
        self.status = value.value

    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}')>"



class ContentChapter(Base):
    __tablename__ = "content_chapters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    title = Column(String(300), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True) # Optional summary for the chapter itself
    audio_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True) # Added video_url if distinct from audio
    duration = Column(Integer, nullable=True)  # Duration of this chapter in seconds
    transcript = Column(Text, nullable=True)    # Transcript for audio/video
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True) # Array of key points or takeaways
    is_preview_allowed = Column(Boolean, default=False) # Can this chapter be previewed for free?
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    content = relationship("Content", back_populates="chapters")
    sections = relationship(
        "ContentSection", 
        back_populates="chapter", 
        cascade="all, delete-orphan",
        order_by="ContentSection.section_order"
    )
    __table_args__ = (
        UniqueConstraint('content_id', 'chapter_number', name='uq_content_chapter_number'),
        Index('idx_content_chapter_content_id_chapter_number', 'content_id', 'chapter_number'),
    )

    def __repr__(self):
        return f"<ContentChapter(id={self.id}, title='{self.title}', chapter_no={self.chapter_number})>"

class ContentSection(Base):
    __tablename__ = "content_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("content_chapters.id"), nullable=False)
    
    title = Column(String(500), nullable=True) # Section title can be optional if it's just a block of text
    body = Column(Text, nullable=False)        # The actual text content of the section
    section_order = Column(Integer, nullable=False, default=0) # For ordering sections within a chapter

    # Optional: if sections can also have their own audio/video snippets
    # audio_url = Column(String(500), nullable=True)
    # video_url = Column(String(500), nullable=True)
    # duration = Column(Integer, nullable=True) 

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    chapter = relationship("ContentChapter", back_populates="sections")

    __table_args__ = (
        UniqueConstraint('chapter_id', 'section_order', name='uq_chapter_section_order'),
        # Consider a unique constraint on chapter_id and title if titles must be unique per chapter
        # UniqueConstraint('chapter_id', 'title', name='uq_chapter_section_title'),
        Index('idx_content_section_chapter_id_order', 'chapter_id', 'section_order'),
    )

    def __repr__(self):
        return f"<ContentSection(id={self.id}, title='{self.title}', order={self.section_order})>"


class ContentTranslation(Base):
    __tablename__ = "content_translation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    language = Column(SQLAlchemyEnum(LanguageCode), nullable=False)
    
    title = Column(String(300), nullable=False)
    subtitle = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    content_body = Column(Text, nullable=True)
    
    translator_name = Column(String(200), nullable=True)
    translation_status = Column(SQLAlchemyEnum(ContentStatus), default=ContentStatus.DRAFT)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    original_content = relationship("Content", back_populates="translations")
    
    __table_args__ = (
        UniqueConstraint('original_content_id', 'language', name='unique_translation_per_language'),
        {'extend_existing': True}
    )