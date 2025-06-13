# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware # Consider if needed for prod


from app.api.v1 import (
    auth, users, homepage, categories,
    place, webhooks, book, s3_upload, lost_heritage
)
     # , admin, places, calendar # Placeholder for future routers

from app.config import settings
from app.database import Base, sync_engine # Use sync_engine for initial table creation
from fastapi.staticfiles import StaticFiles

# Create database tables (using sync engine for this one-off task)
# In a production setup with Alembic, you might not do this here.
# Base.metadata.create_all(bind=sync_engine) 
# Commenting out: prefer Alembic for schema management

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for Sanatani - Spiritual Content Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json" # Good practice for versioned OpenAPI
)

# Mount static files directory
# Create the 'uploads' directory if it doesn't exist at the root of your project
# (relative to where uvicorn is run, or use absolute path from settings)
upload_dir_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR) # Simple relative path
if not os.path.exists(upload_dir_path):
    os.makedirs(upload_dir_path)

app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")


# Middleware
app.add_middleware(
    CORSMiddleware,
    #allow_origins=[str(origin) for origin in settings.ALLOWED_HOSTS] if settings.ALLOWED_HOSTS else ["*"],
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:8000",
        "https://project-guruji-2or4.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS if settings.ALLOWED_HOSTS else ["*"])


# API Routes
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"]) # Add this
app.include_router(book.router, prefix="/api/v1/books", tags=["Books"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(homepage.router, prefix="/api/v1/homepage", tags=["Homepage Features"])
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"]) # Placeholder
app.include_router(place.router, prefix="/api/v1/places", tags=["Places"]) # Placeholder
app.include_router(lost_heritage.router, prefix="/api/v1/lost_heritage", tags=["Lost Heritage"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"]) # Placeholder
app.include_router(s3_upload.router, prefix="/api/v1/s3_upload", tags=["S3 Upload"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    # Add database connectivity check here if desired
    return {"status": "healthy"}

# Example of how to run with uvicorn for development:
# uvicorn app.main:app --reload