# app/crud/user.py
from typing import Optional, Union
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
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
            role=obj_in.role,
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
        if "password" in update_data: # This should not happen if UserUpdate doesn't have password
            del update_data["password"] # Or raise error
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)


user_crud = CRUDUser(User)