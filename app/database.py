# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings

# ----------------------
# Base class for SQLAlchemy models
# ----------------------
Base = declarative_base()

# ----------------------
# Sync Engine & Session (kept for Alembic or specific sync tasks if needed)
# ----------------------
#sync_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
#SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Sync Engine & Session (SQLite specific tweak)
sync_engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# ----------------------
# Async Engine & Session
# ----------------------
if not settings.DATABASE_URL_ASYNC:
    raise ValueError("DATABASE_URL_ASYNC must be configured in settings for asynchronous operations.")

#async_engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False) # echo=True for dev SQL logging
#AsyncSessionLocal = async_sessionmaker(
#    bind=async_engine, class_=AsyncSession, expire_on_commit=False
#)
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL_ASYNC else {},
)

# Use async_sessionmaker for async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# ----------------------
# Async DB Dependency
# ----------------------
async def get_async_db() -> AsyncSession: # Changed return type hint
    async with AsyncSessionLocal() as session:
        yield session

# ----------------------
# Sync DB Dependency (for Alembic or rare sync needs)
# ----------------------
def get_db_sync():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()