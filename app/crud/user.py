# app/crud/user.py
from typing import Optional, Union
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy import func, or_

from app.crud.base import CRUDBase
from app.models.user import User, UserRole
from datetime import datetime
from app.schemas.user import UserCreate, UserUpdate, AdminCreate
from app.utils.security import get_password_hash

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):

    async def get_user(self, db: AsyncSession, user_id: PyUUID) -> Optional[User]:
        # The base 'get' method already handles UUID, int, str.
        # If user_id from JWT is always a string, convert it before calling base.
        # Here, assuming user_id is already PyUUID as per dependencies.py change.
        return await super().get(db, id=user_id)

    async def get_user_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .filter(User.email == email)
            .filter(User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        if not username: return None
        result = await db.execute(
            select(User)
            .filter(User.username == username)
            .filter(User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def update_user(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
    ) -> User:

        # Example: if password needs to be updated, it should be handled separately
        # and not directly through CRUDBase.update if obj_in contains plain password
        update_data = obj_in.model_dump(exclude_unset=True)
        update_data["role"] = obj_in.role.value if obj_in.role is not None else db_obj.role.value # Ensure role is set correctly
        if "password" in update_data: # This should not happen if UserUpdate doesn't have password
            del update_data["password"] # Or raise error

        # Handle role update specifically
        if "role" in update_data and update_data["role"] is not None:
            # Ensure the role value is valid (e.g., from your UserRole enum)
            try:
                role_value = UserRole(update_data["role"]).value # Validate and get string value
                setattr(db_obj, "role", role_value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid role: {update_data['role']}")
            del update_data["role"] # Remove from dict if handled separately

        # Apply other updates
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_user_by_clerk_id(self, db: AsyncSession, *, clerk_user_id: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .filter(User.clerk_user_id == clerk_user_id)
            .filter(User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    # This create_user is now primarily for webhook handling or admin creation
    async def create_user_from_clerk(
        self, db: AsyncSession, *, clerk_data: dict # Data from Clerk webhook or API
    ) -> User:
        # Extract relevant fields from clerk_data
        clerk_user_id = clerk_data.get("id") # Clerk's user ID
        email_addresses = clerk_data.get("email_addresses", [])
        primary_email_obj = next((e for e in email_addresses if e.get("id") == clerk_data.get("primary_email_address_id")), None)
        email = primary_email_obj.get("email_address") if primary_email_obj else None

        if not email or not clerk_user_id:
            raise ValueError("Clerk ID and primary email are required to create user.")

        # Check if user with this email or clerk_id already exists (idempotency for webhooks)
        existing_by_clerk_id = await self.get_user_by_clerk_id(db, clerk_user_id=clerk_user_id)
        if existing_by_clerk_id:
            return existing_by_clerk_id # Or update it
        
        existing_by_email = await self.get_user_by_email(db, email=email)
        if existing_by_email:
            # This case needs careful handling: email exists but clerk_id doesn't match.
            # Could be an old account, or an attempt to link.
            # For now, let's assume we update the existing user with the clerk_id if it's missing.
            if not existing_by_email.clerk_user_id:
                existing_by_email.clerk_user_id = clerk_user_id
                # Sync other fields from clerk_data to existing_by_email
                existing_by_email.first_name = clerk_data.get("first_name")
                existing_by_email.last_name = clerk_data.get("last_name")
                existing_by_email.avatar_url = clerk_data.get("image_url") # Or profile_image_url
                # ... sync other relevant fields ...
                db.add(existing_by_email)
                await db.commit()
                await db.refresh(existing_by_email)
                return existing_by_email
            else:
                # Email exists and is already linked to a different Clerk ID. This is an issue.
                raise ValueError(f"Email {email} already associated with a different Clerk user.")


        db_obj = User(
            clerk_user_id=clerk_user_id,
            email=email,
            # Password is not set here; Clerk manages it
            username=clerk_data.get("username"), # If username is available and unique
            first_name=clerk_data.get("first_name"),
            last_name=clerk_data.get("last_name"),
            avatar_url=clerk_data.get("image_url"), # Clerk uses image_url or profile_image_url
            # Set default role or other app-specific fields
            role=UserRole.USER.value, 
            is_active=True, # Assume active from Clerk
            is_verified=primary_email_obj.get("verification", {}).get("status") == "verified" if primary_email_obj else False,
            email_verified_at=datetime.fromtimestamp(primary_email_obj.get("verification", {}).get("verified_at_server")) if primary_email_obj and primary_email_obj.get("verification", {}).get("status") == "verified" and primary_email_obj.get("verification", {}).get("verified_at_server") else None,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_user_from_clerk(self, db: AsyncSession, *, clerk_user_id: str, clerk_data: dict) -> Optional[User]:
        db_user = await self.get_user_by_clerk_id(db, clerk_user_id=clerk_user_id)
        if not db_user:
            return None # Should ideally not happen if create webhook was processed

        # Update fields from clerk_data
        email_addresses = clerk_data.get("email_addresses", [])
        primary_email_obj = next((e for e in email_addresses if e.get("id") == clerk_data.get("primary_email_address_id")), None)
        
        db_user.email = primary_email_obj.get("email_address") if primary_email_obj else db_user.email
        db_user.first_name = clerk_data.get("first_name", db_user.first_name)
        db_user.last_name = clerk_data.get("last_name", db_user.last_name)
        db_user.username = clerk_data.get("username", db_user.username)
        db_user.avatar_url = clerk_data.get("image_url", db_user.avatar_url)
        
        if primary_email_obj:
            db_user.is_verified = primary_email_obj.get("verification", {}).get("status") == "verified"
            if db_user.is_verified and primary_email_obj.get("verification").get("verified_at_server"):
                db_user.email_verified_at = datetime.fromtimestamp(primary_email_obj.get("verification").get("verified_at_server") / 1000) # Clerk timestamps might be in ms


        # Handle potential 'deleted' status from Clerk if it comes in user.updated
        # if clerk_data.get("deleted", False):
        #    db_user.is_active = False 
        # Or handle user.deleted webhook separately to hard delete or deactivate.

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    async def get_users_list_and_count(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> list[User]:
        query = select(User).filter(User.is_deleted.is_(False)).order_by(User.created_at.desc())
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        # Apply pagination
        total_count_query = select(func.count(User.id)).filter(User.is_deleted.is_(False))
        if search:
            total_count_query = total_count_query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        total_count_result = await db.execute(total_count_query)
        total_count = total_count_result.scalar_one()

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total_count
    


user_crud = CRUDUser(User)