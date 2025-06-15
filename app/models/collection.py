# app/models/collection.py
from sqlalchemy import (
    Column, String, Text, Boolean, ForeignKey, Integer, DateTime, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User # Assuming User model exists for curator_id
from app.models.content import Content # Assuming Content model exists for content_id

class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), unique=True, nullable=False, index=True) # Ensure slug generation
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, index=True)
    
    #curator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Optional curator
    
    tags = Column(JSON, nullable=True) # Example: ["spirituality", "beginners"]
    sort_order = Column(Integer, default=0) # For ordering collections themselves if needed

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    #curator = relationship("User", backref="curated_collections") # Relationship to User
    items = relationship(
        "CollectionItem", 
        back_populates="collection", 
        cascade="all, delete-orphan", 
        order_by="CollectionItem.sort_order" # Order items within a collection
    )
    
    def __repr__(self):
        return f"<Collection(id='{self.id}', name='{self.name}')>"

class CollectionItem(Base):
    __tablename__ = "collection_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False, index=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False, index=True) # Points to a Content item
    
    sort_order = Column(Integer, default=0, nullable=False) # Order of this item within the collection
    notes = Column(Text, nullable=True) # Curator's notes about this specific item in this collection
    
    added_at = Column(DateTime, default=func.now(), nullable=False)

    collection = relationship("Collection", back_populates="items")
    # content_item = relationship("Content", backref="collection_entries") # Relationship to Content model
    # Using a simple relationship. If you need to navigate from Content to CollectionItem:
    content = relationship("Content") # This allows access to the Content object via item.content

    __table_args__ = (
        #UniqueConstraint('collection_id', 'content_id', name='uq_collection_content_item'),
        # sort_order doesn't need to be unique globally, but might be per collection if you enforce it.
        #UniqueConstraint('collection_id', 'sort_order', name='uq_collection_item_sort_order'), # Consider if needed
        Index('idx_collection_item_collection_order', 'collection_id', 'sort_order'),
    )

    def __repr__(self):
        return f"<CollectionItem(id='{self.id}', collection_id='{self.collection_id}', content_id='{self.content_id}')>"