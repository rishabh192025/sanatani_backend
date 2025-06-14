from app.database import Base
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum, JSON, LargeBinary, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Country(Base):
    __tablename__ = "countries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    regions = relationship("Region", back_populates="country")
    places = relationship("Place", back_populates="country")


class Region(Base):
    __tablename__ = "regions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"))
    country = relationship("Country", back_populates="regions")
    states = relationship("State", back_populates="region")
    places = relationship("Place", back_populates="region")


class State(Base):
    __tablename__ = "states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"))
    region = relationship("Region", back_populates="states")
    cities = relationship("City", back_populates="state")
    places = relationship("Place", back_populates="state")


class City(Base):
    __tablename__ = "cities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)       # city names cant be unique as two aurangabad etc.
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"))
    state = relationship("State", back_populates="cities")
    places = relationship("Place", back_populates="city")