# app/utils/helpers.py
import re
import uuid
from typing import Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import Base # Assuming Base is defined in app.database

ModelType = Type[Base]

def slugify(text: str) -> str:
    """
    Generate a basic slug from text.
    Converts to lowercase, removes non-alphanumeric characters,
    and replaces spaces with hyphens.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)  # Remove non-alphanumeric except hyphens and spaces
    text = re.sub(r'[\s_-]+', '-', text) # Replace spaces and underscores with a single hyphen
    text = text.strip('-') # Remove leading/trailing hyphens
    return text

async def generate_unique_slug(
    db: AsyncSession,
    model: ModelType,
    title: str,
    current_id: Optional[uuid.UUID] = None
) -> str:
    """
    Generates a unique slug for a given title.
    If a slug already exists, it appends a short UUID.
    `current_id` is used during updates to allow the same slug if it belongs to the current item.
    """
    base_slug = slugify(title)
    if not base_slug: # Handle empty title case
        base_slug = str(uuid.uuid4())[:8] # Generate a random slug if title is empty

    slug_candidate = base_slug
    attempt = 0

    while True:
        query = select(model).filter(model.slug == slug_candidate)
        if current_id:
            query = query.filter(model.id != current_id)
        
        existing = await db.execute(query)
        if existing.scalar_one_or_none() is None:
            return slug_candidate
        
        attempt += 1
        # Append a short random string or a counter if collision
        # Using short uuid part for better uniqueness than simple counter
        slug_candidate = f"{base_slug}-{str(uuid.uuid4())[:4]}"
        if attempt > 5: # Safety break to prevent infinite loop in extreme cases
            slug_candidate = f"{base_slug}-{str(uuid.uuid4())[:8]}" # Longer random part
            # Check one last time or raise an error
            query_final = select(model).filter(model.slug == slug_candidate)
            if current_id:
                query_final = query_final.filter(model.id != current_id)
            existing_final = await db.execute(query_final)
            if existing_final.scalar_one_or_none() is None:
                return slug_candidate
            else: # Extremely unlikely, but possible
                return f"{base_slug}-{uuid.uuid4()}" # Fallback to full UUID


# Alias for direct use in CRUD if preferred
async def generate_slug(db: AsyncSession, model: ModelType, title: str, current_id: Optional[uuid.UUID] = None) -> str:
    return await generate_unique_slug(db, model, title, current_id)