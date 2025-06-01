from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Enum, JSON, LargeBinary, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

# Enums
class UserRole(PyEnum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"

class ContentStatus(PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"

class LanguageCode(PyEnum):
    EN = "en"
    HI = "hi"
    SA = "sa"  # Sanskrit
    BN = "bn"  # Bengali
    TA = "ta"  # Tamil
    TE = "te"  # Telugu
    MR = "mr"  # Marathi
    GU = "gu"  # Gujarati

class PlaceType(PyEnum):
    TEMPLE = "temple"
    ASHRAM = "ashram"
    PILGRIMAGE_SITE = "pilgrimage_site"
    ANCIENT_RUINS = "ancient_ruins"
    SACRED_GROVE = "sacred_grove"
    RIVER_GHAT = "river_ghat"
    MOUNTAIN_PEAK = "mountain_peak"

class ContentType(PyEnum):
    BOOK = "book"
    AUDIOBOOK = "audiobook"
    VIDEO = "video"
    ARTICLE = "article"
    PODCAST = "podcast"

class EventType(PyEnum):
    FESTIVAL = "festival"
    AUSPICIOUS_DAY = "auspicious_day"
    LUNAR_EVENT = "lunar_event"
    SOLAR_EVENT = "solar_event"
    RELIGIOUS_OBSERVANCE = "religious_observance"

# Core User Management
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    
    # Spiritual Profile
    spiritual_name = Column(String(150), nullable=True)
    guru_lineage = Column(String(200), nullable=True)
    meditation_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    preferred_practices = Column(JSON, nullable=True)  # Array of practice types
    
    # Location & Preferences
    country = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    preferred_language = Column(Enum(LanguageCode), default=LanguageCode.EN)
    
    # Account Management
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    # Subscription & Access
    subscription_tier = Column(String(50), default="free")  # free, premium, lifetime
    subscription_starts_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_content = relationship("Content", back_populates="author", foreign_keys="Content.author_id")
    user_progress = relationship("UserProgress", back_populates="user")
    bookmarks = relationship("UserBookmark", back_populates="user")
    reviews = relationship("ContentReview", back_populates="user")

# Content Management System
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    color_code = Column(String(7), nullable=True)  # Hex color
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Self-referential relationship for hierarchical categories
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    content = relationship("Content", back_populates="category")

class Content(Base):
    __tablename__ = "content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False, index=True)
    slug = Column(String(350), unique=True, nullable=False, index=True)
    subtitle = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    content_body = Column(Text, nullable=True)  # For articles, stories
    
    # Content Classification
    content_type = Column(Enum(ContentType), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tag strings
    language = Column(Enum(LanguageCode), default=LanguageCode.EN, nullable=False)
    
    # Media & Files
    cover_image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)  # PDF, audio, video file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Integer, nullable=True)  # Duration in seconds for audio/video
    page_count = Column(Integer, nullable=True)  # For books
    
    # Author & Attribution
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    author_name = Column(String(200), nullable=True)  # For traditional/historical authors
    translator = Column(String(200), nullable=True)
    narrator = Column(String(200), nullable=True)  # For audiobooks
    
    # Publishing & Status
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT, nullable=False)
    published_at = Column(DateTime, nullable=True)
    featured = Column(Boolean, default=False)
    premium_content = Column(Boolean, default=False)
    
    # Engagement Metrics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)
    
    # SEO & Discovery
    meta_title = Column(String(160), nullable=True)
    meta_description = Column(String(320), nullable=True)
    keywords = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="created_content", foreign_keys=[author_id])
    category = relationship("Category", back_populates="content")
    chapters = relationship("ContentChapter", back_populates="content")
    reviews = relationship("ContentReview", back_populates="content")
    user_progress = relationship("UserProgress", back_populates="content")
    translations = relationship("ContentTranslation", back_populates="original_content")

class ContentChapter(Base):
    __tablename__ = "content_chapters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    title = Column(String(300), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    content_body = Column(Text, nullable=True)
    
    # For Audio Chapters
    audio_url = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    transcript = Column(Text, nullable=True)
    
    # Chapter specific metadata
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    content = relationship("Content", back_populates="chapters")
    
    __table_args__ = (
        UniqueConstraint('content_id', 'chapter_number', name='unique_chapter_per_content'),
        Index('idx_content_chapter', 'content_id', 'chapter_number'),
    )

class ContentTranslation(Base):
    __tablename__ = "content_translations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    language = Column(Enum(LanguageCode), nullable=False)
    
    title = Column(String(300), nullable=False)
    subtitle = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    content_body = Column(Text, nullable=True)
    
    translator_name = Column(String(200), nullable=True)
    translation_status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    original_content = relationship("Content", back_populates="translations")
    
    __table_args__ = (
        UniqueConstraint('original_content_id', 'language', name='unique_translation_per_language'),
    )

# Sacred Places & Geography
class SacredPlace(Base):
    __tablename__ = "sacred_places"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    alternate_names = Column(JSON, nullable=True)  # Array of alternative names
    place_type = Column(Enum(PlaceType), nullable=False, index=True)
    
    # Location Details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), nullable=True)
    
    # Geographic Coordinates
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)  # meters above sea level
    
    # Detailed Information
    description = Column(Text, nullable=True)
    history = Column(Text, nullable=True)
    significance = Column(Text, nullable=True)
    legends_stories = Column(Text, nullable=True)
    
    # Temple/Place Specific
    deity_names = Column(JSON, nullable=True)  # Primary deities
    architectural_style = Column(String(100), nullable=True)
    built_year = Column(Integer, nullable=True)
    built_century = Column(String(50), nullable=True)  # "12th century BCE"
    dynasty_period = Column(String(100), nullable=True)
    
    # Visitor Information
    visiting_hours = Column(JSON, nullable=True)  # Structured schedule
    entry_fee = Column(JSON, nullable=True)  # Different categories
    dress_code = Column(Text, nullable=True)
    special_rituals = Column(JSON, nullable=True)
    festivals_celebrated = Column(JSON, nullable=True)
    
    # Media
    images = Column(JSON, nullable=True)  # Array of image URLs
    videos = Column(JSON, nullable=True)  # Array of video URLs
    virtual_tour_url = Column(String(500), nullable=True)
    
    # Status & Verification
    verification_status = Column(String(50), default="pending")  # verified, pending, disputed
    is_active = Column(Boolean, default=True)
    accessibility_info = Column(JSON, nullable=True)
    
    # Engagement
    visit_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    pilgrimage_routes = relationship("PilgrimageRoutePlace", back_populates="place")
    
    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_place_country_type', 'country', 'place_type'),
    )

class PilgrimageRoute(Base):
    __tablename__ = "pilgrimage_routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    significance = Column(Text, nullable=True)
    
    # Route Details
    total_distance = Column(Float, nullable=True)  # kilometers
    estimated_duration = Column(Integer, nullable=True)  # days
    difficulty_level = Column(String(20), nullable=True)  # easy, moderate, difficult
    best_season = Column(String(100), nullable=True)
    
    # Route Path (GeoJSON or array of coordinates)
    route_path = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    places = relationship("PilgrimageRoutePlace", back_populates="route")

class PilgrimageRoutePlace(Base):
    __tablename__ = "pilgrimage_route_places"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("pilgrimage_routes.id"), nullable=False)
    place_id = Column(UUID(as_uuid=True), ForeignKey("sacred_places.id"), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    
    # Stop-specific information
    recommended_stay_duration = Column(Integer, nullable=True)  # hours
    special_instructions = Column(Text, nullable=True)
    accommodation_info = Column(JSON, nullable=True)
    
    route = relationship("PilgrimageRoute", back_populates="places")
    place = relationship("SacredPlace", back_populates="pilgrimage_routes")
    
    __table_args__ = (
        UniqueConstraint('route_id', 'place_id', name='unique_route_place'),
        Index('idx_route_sequence', 'route_id', 'sequence_order'),
    )

# Calendar & Events System
class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    sanskrit_name = Column(String(200), nullable=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    
    # Date & Time (supports both solar and lunar calendars)
    gregorian_date = Column(DateTime, nullable=True)
    lunar_date = Column(String(50), nullable=True)  # "Chaitra Shukla Navami"
    tithi = Column(String(50), nullable=True)
    nakshatra = Column(String(50), nullable=True)
    yoga = Column(String(50), nullable=True)
    karana = Column(String(50), nullable=True)
    
    # Event Details
    description = Column(Text, nullable=True)
    significance = Column(Text, nullable=True)
    rituals = Column(JSON, nullable=True)  # Array of ritual descriptions
    observances = Column(JSON, nullable=True)  # What devotees should do
    
    # Timing
    is_recurring = Column(Boolean, default=True)
    duration_days = Column(Integer, default=1)
    auspicious_timings = Column(JSON, nullable=True)  # Muhurat timings
    
    # Regional Variations
    regional_names = Column(JSON, nullable=True)  # Different names in different regions
    regional_customs = Column(JSON, nullable=True)
    
    # Media
    images = Column(JSON, nullable=True)
    associated_mantras = Column(JSON, nullable=True)
    
    # Geographic Relevance
    applicable_regions = Column(JSON, nullable=True)  # Where this event is celebrated
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_event_date_type', 'gregorian_date', 'event_type'),
    )

# Panchang System
class PanchangData(Base):
    __tablename__ = "panchang_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Five elements of Panchang
    tithi = Column(String(50), nullable=False)  # Lunar day
    vara = Column(String(20), nullable=False)   # Day of week
    nakshatra = Column(String(50), nullable=False)  # Star constellation
    yoga = Column(String(50), nullable=False)   # Auspicious combination
    karana = Column(String(50), nullable=False) # Half lunar day
    
    # Timing Details
    sunrise_time = Column(String(10), nullable=True)
    sunset_time = Column(String(10), nullable=True)
    moonrise_time = Column(String(10), nullable=True)
    moonset_time = Column(String(10), nullable=True)
    
    # Auspicious Timings
    abhijit_muhurat = Column(String(20), nullable=True)
    rahu_kaal = Column(String(20), nullable=True)
    gulika_kaal = Column(String(20), nullable=True)
    yamaganda_kaal = Column(String(20), nullable=True)
    
    # Additional Information
    paksha = Column(String(20), nullable=True)  # Shukla/Krishna
    ritu = Column(String(20), nullable=True)    # Season
    masa = Column(String(30), nullable=True)    # Hindu month
    samvatsara = Column(String(30), nullable=True)  # Hindu year
    
    # Location-specific (can be extended for multiple cities)
    location_name = Column(String(100), default="General")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())

# User Engagement & Progress Tracking
class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    
    # Progress Tracking
    progress_percentage = Column(Float, default=0.0)  # 0-100
    current_position = Column(Integer, default=0)  # Current page/timestamp
    total_duration = Column(Integer, nullable=True)  # Total content duration
    time_spent = Column(Integer, default=0)  # Time spent in seconds
    
    # Reading/Listening State
    is_completed = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    last_accessed_at = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    
    # User Notes & Highlights
    notes = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)  # Array of highlighted sections
    personal_rating = Column(Integer, nullable=True)  # 1-5 stars
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="user_progress")
    content = relationship("Content", back_populates="user_progress")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'content_id', name='unique_user_content_progress'),
    )

class UserBookmark(Base):
    __tablename__ = "user_bookmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    
    bookmark_type = Column(String(50), default="content")  # content, place, event
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="bookmarks")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'content_id', name='unique_user_bookmark'),
    )

class ContentReview(Base):
    __tablename__ = "content_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text, nullable=True)
    is_verified_purchase = Column(Boolean, default=False)
    
    # Review Moderation
    is_approved = Column(Boolean, default=True)
    moderated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    moderation_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="reviews", foreign_keys=[user_id])
    content = relationship("Content", back_populates="reviews")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'content_id', name='unique_user_review'),
    )

# Collections & Curated Content
class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    
    # Collection Properties
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    curator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    items = relationship("CollectionItem", back_populates="collection")

class CollectionItem(Base):
    __tablename__ = "collection_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    
    sort_order = Column(Integer, default=0)
    notes = Column(Text, nullable=True)  # Curator's notes about this item
    
    created_at = Column(DateTime, default=func.now())
    
    collection = relationship("Collection", back_populates="items")
    
    __table_args__ = (
        UniqueConstraint('collection_id', 'content_id', name='unique_collection_content'),
    )

# Meditation & Spiritual Practices
class MeditationSession(Base):
    __tablename__ = "meditation_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session Details
    session_name = Column(String(200), nullable=True)
    meditation_type = Column(String(100), nullable=True)  # guided, silent, mantra, etc.
    duration_minutes = Column(Integer, nullable=False)
    
    # Session Data
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    actual_duration = Column(Integer, nullable=True)  # Actual time spent
    
    # Session Experience
    mood_before = Column(String(50), nullable=True)
    mood_after = Column(String(50), nullable=True)
    experience_notes = Column(Text, nullable=True)
    quality_rating = Column(Integer, nullable=True)  # 1-10
    
    # Guided Session Reference
    guided_content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())

# System Configuration & Settings
class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # general, email, storage, etc.
    
    is_public = Column(Boolean, default=False)  # Can be accessed by frontend
    requires_restart = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

# Audit & Activity Logging
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Activity Details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)  # user, content, place, etc.
    resource_id = Column(String(100), nullable=True)
    
    # Context
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Request Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_activity_user_action', 'user_id', 'action'),
        Index('idx_activity_resource', 'resource_type', 'resource_id'),
    )

# File Management
class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)
    
    # File Properties
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication
    
    # Upload Context
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    upload_purpose = Column(String(100), nullable=True)  # avatar, content, cover, etc.
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    # File Status
    is_processed = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Storage Information
    storage_provider = Column(String(50), default="local")  # local, s3, cloudinary
    storage_path = Column(String(500), nullable=True)
    cdn_url = Column(String(500), nullable=True)
    
    # Metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # For audio/video
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_file_hash', 'file_hash'),
        Index('idx_file_entity', 'related_entity_type', 'related_entity_id'),
    )

# Notification System
class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    template_type = Column(String(50), nullable=False)  # email, push, sms, in_app
    
    # Template Content
    subject = Column(String(200), nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    
    # Template Variables
    variables = Column(JSON, nullable=True)  # Available template variables
    
    # Localization
    language = Column(Enum(LanguageCode), default=LanguageCode.EN)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserNotification(Base):
    __tablename__ = "user_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notification Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # info, success, warning, error
    
    # Notification Context
    action_url = Column(String(500), nullable=True)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Delivery
    delivery_method = Column(String(50), default="in_app")  # in_app, email, push
    delivered_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_user_notifications', 'user_id', 'is_read'),
    )

# Analytics and Reporting
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Event Details
    event_name = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=True)
    event_action = Column(String(100), nullable=True)
    event_label = Column(String(200), nullable=True)
    
    # Event Properties
    properties = Column(JSON, nullable=True)
    value = Column(Float, nullable=True)
    
    # Context
    page_url = Column(String(500), nullable=True)
    referrer_url = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Geographic
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Device Information
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_analytics_event_time', 'event_name', 'created_at'),
        Index('idx_analytics_user_event', 'user_id', 'event_name'),
    )

# Content Recommendations
class RecommendationEngine(Base):
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    
    # Recommendation Details
    recommendation_type = Column(String(50), nullable=False)  # collaborative, content_based, trending
    score = Column(Float, nullable=False)  # Recommendation confidence score
    reason = Column(String(200), nullable=True)  # Why this was recommended
    
    # Recommendation Context
    context = Column(JSON, nullable=True)  # Additional context data
    algorithm_version = Column(String(20), default="1.0")
    
    # User Interaction
    is_clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_user_recommendations', 'user_id', 'score'),
        UniqueConstraint('user_id', 'content_id', 'recommendation_type', name='unique_user_content_recommendation'),
    )

# Search & Discovery
class SearchQuery(Base):
    __tablename__ = "search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Query Details
    query_text = Column(String(500), nullable=False, index=True)
    normalized_query = Column(String(500), nullable=True)  # Cleaned/normalized version
    language = Column(Enum(LanguageCode), nullable=True)
    
    # Search Context
    search_type = Column(String(50), default="general")  # general, content, places, events
    filters_applied = Column(JSON, nullable=True)
    sort_order = Column(String(50), nullable=True)
    
    # Results
    results_count = Column(Integer, default=0)
    results_clicked = Column(Integer, default=0)
    first_result_clicked = Column(Boolean, default=False)
    
    # Performance
    response_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_search_query_time', 'query_text', 'created_at'),
    )

# Subscription & Payment Management
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    plan_code = Column(String(50), unique=True, nullable=False)
    
    # Plan Details
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)  # Array of feature descriptions
    limitations = Column(JSON, nullable=True)  # Usage limits
    
    # Pricing
    price_monthly = Column(Float, nullable=True)
    price_yearly = Column(Float, nullable=True)
    price_lifetime = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    
    # Plan Configuration
    max_downloads = Column(Integer, nullable=True)
    max_bookmarks = Column(Integer, nullable=True)
    offline_access = Column(Boolean, default=False)
    premium_content_access = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    
    # Subscription Details
    status = Column(String(50), nullable=False)  # active, cancelled, expired, paused
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly, lifetime
    
    # Dates
    started_at = Column(DateTime, nullable=False)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Billing
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50), nullable=True)
    
    # External References
    stripe_subscription_id = Column(String(100), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    
    # Auto-renewal
    auto_renewal = Column(Boolean, default=True)
    renewal_reminder_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_user_subscription_status', 'user_id', 'status'),
    )

# API Keys & Integrations
class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Key Details
    key_name = Column(String(100), nullable=False)
    api_key = Column(String(100), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Permissions & Scope
    scopes = Column(JSON, nullable=True)  # Array of allowed scopes
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Usage Tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_api_key_user', 'user_id', 'is_active'),
    )

# Feedback & Support
class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Feedback Details
    feedback_type = Column(String(50), nullable=False)  # bug, feature, general
    category = Column(String(100), nullable=True)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Contact Information (for anonymous feedback)
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(100), nullable=True)
    
    # Context
    page_url = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    
    # Status & Response
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_feedback_status', 'status', 'priority'),
    )

# Content Moderation
class ModerationQueue(Base):
    __tablename__ = "moderation_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content Details
    content_type = Column(String(50), nullable=False)  # content, review, comment
    content_id = Column(UUID(as_uuid=True), nullable=False)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Report Details
    reason = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="medium")  # low, medium, high
    
    # Moderation Status
    status = Column(String(50), default="pending")  # pending, reviewing, approved, rejected
    moderator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    moderation_notes = Column(Text, nullable=True)
    action_taken = Column(String(100), nullable=True)  # approved, hidden, deleted, etc.
    
    created_at = Column(DateTime, default=func.now())
    moderated_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_moderation_status', 'status', 'severity'),
        Index('idx_moderation_content', 'content_type', 'content_id'),
    )

# Database Indexes for Performance
# Additional indexes can be created as needed:

# For full-text search on content
# CREATE INDEX idx_content_search ON content USING gin(to_tsvector('english', title || ' ' || description));

# For geospatial queries on sacred places
# CREATE INDEX idx_places_location ON sacred_places USING gist(st_point(longitude, latitude));

# For efficient user activity queries
# CREATE INDEX idx_activity_user_time ON activity_logs(user_id, created_at DESC);

# For content recommendations
# CREATE INDEX idx_recommendations_active ON recommendations(user_id, expires_at) WHERE is_dismissed = false;