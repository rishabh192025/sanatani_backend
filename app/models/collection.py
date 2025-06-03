# app/models/collection.py
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func

from app.database import Base
# from app.models.user import User # Uncomment if curator_id is used
from app.models.content import Content # Required for CollectionItem.content_item

class Collection(Base):
    __tablename__ = "collections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, index=True)
    # curator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Optional
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # curator = relationship("User", backref="curated_collections") # Optional
    items = relationship(
        "CollectionItem", 
        back_populates="collection", 
        cascade="all, delete-orphan", 
        order_by="CollectionItem.sort_order"
    )
    
    def __repr__(self):
        return f"<Collection(id='{self.id}', name='{self.name}')>"

class CollectionItem(Base):
    __tablename__ = "collection_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=func.now(), nullable=False)

    collection = relationship("Collection", back_populates="items")
    content_item = relationship("Content") # Simple relationship to Content, backref can be added to Content model if needed

    __table_args__ = (
        UniqueConstraint('collection_id', 'content_id', name='uq_collection_content_item'),
        UniqueConstraint('collection_id', 'sort_order', name='uq_collection_item_sort_order'), # Ensures unique sort order per collection
        Index('idx_collection_item_collection_id_order', 'collection_id', 'sort_order'),
    )

    def __repr__(self):
        return f"<CollectionItem(id='{self.id}', collection_id='{self.collection_id}', content_id='{self.content_id}')>"