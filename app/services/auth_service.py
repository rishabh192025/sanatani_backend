# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from fastapi import HTTPException, status
from uuid import UUID

from app.crud.user import user_crud
from app.schemas.auth import UserLogin
from app.schemas.user import UserCreate # For registration
from app.utils.security import verify_password, create_access_token, create_refresh_token
from app.models.user import User

class AuthService:
    async def authenticate_user(self, db: AsyncSession, login_data: UserLogin) -> User | None:
        user = await user_crud.get_user_by_email(db, email=login_data.email)
        if not user:
            return None
        if not verify_password(login_data.password, user.hashed_password): # verify_password is sync
            return None
        if not user.is_active:
            raise HTTPException(status_code=400, detail="User account is inactive.")
        return user

    def generate_tokens(self, user_id: UUID) -> tuple[str, str]: # user_id is UUID
        # JWT creation is CPU-bound and sync, so it's fine here
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return access_token, refresh_token
    
    async def register_new_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        existing_user_email = await user_crud.get_user_by_email(db, email=user_in.email)
        if existing_user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )
        if user_in.username:
            existing_user_username = await user_crud.get_user_by_username(db, username=user_in.username)
            if existing_user_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This username is already taken.",
                )
        
        user = await user_crud.create_user(db, obj_in=user_in)
        return user

auth_service = AuthService()