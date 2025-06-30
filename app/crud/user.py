# app/crud/user.py
from typing import Optional, Union
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

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
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        if not username: return None
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password), # Password hashing is sync
            username=obj_in.username,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            is_active=obj_in.is_active if obj_in.is_active is not None else True,
            is_verified=obj_in.is_verified if obj_in.is_verified is not None else False,
            role=UserRole.USER.value,  # Default role, can be changed later
            preferred_language=obj_in.preferred_language
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_admin_user(self, db: AsyncSession, *, obj_in: AdminCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password), # Password hashing is sync
            username=obj_in.username,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            is_active=obj_in.is_active if obj_in.is_active is not None else True,
            is_verified=obj_in.is_verified if obj_in.is_verified is not None else False,
            role=UserRole.ADMIN.value,  # Default role, can be changed later
            preferred_language=obj_in.preferred_language
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # update method can be inherited from CRUDBase if standard update is sufficient
    # If specific logic is needed for user update (e.g., password change), implement here
    async def update_user(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        # Example: if password needs to be updated, it should be handled separately
        # and not directly through CRUDBase.update if obj_in contains plain password
        update_data = obj_in.model_dump(exclude_unset=True)
        update_data["role"] = obj_in.role.value if obj_in.role is not None else db_obj.role.value # Ensure role is set correctly
        if "password" in update_data: # This should not happen if UserUpdate doesn't have password
            del update_data["password"] # Or raise error
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def get_user_by_clerk_id(self, db: AsyncSession, *, clerk_user_id: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.clerk_user_id == clerk_user_id))
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
            email_verified_at=datetime.fromtimestamp(primary_email_obj.get("verification").get("verified_at_server")) if primary_email_obj and primary_email_obj.get("verification", {}).get("status") == "verified" and primary_email_obj.get("verification").get("verified_at_server") else None,
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


user_crud = CRUDUser(User)