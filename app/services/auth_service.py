# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from fastapi import HTTPException, status
from uuid import UUID

from app.crud import user_crud, book_crud, teaching_crud, place_crud, temple_crud, festival_crud, story_crud
from app.schemas.auth import UserLogin, OverviewResponse
from app.schemas.user import UserCreate, AdminCreate # For registration
from app.utils.security import verify_password, create_access_token, create_refresh_token
from app.models.user import User

class AuthService:
    async def authenticate_admin_user(self, db: AsyncSession, login_data: UserLogin) -> User | None:
        user = await user_crud.get_user_by_email(db, email=login_data.email)
        if not user:
            return None
        if not verify_password(login_data.password, user.hashed_password): # verify_password is sync
            return None
        if user.is_deleted:
            raise HTTPException(status_code=400, detail="User account is inactive.")
        return user

    def generate_tokens(self, user_id: UUID) -> tuple[str, str]: # user_id is UUID
        # JWT creation is CPU-bound and sync, so it's fine here
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return access_token, refresh_token
    
    async def register_new_admin_user(self, db: AsyncSession, user_in: AdminCreate) -> User:
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
        
        user = await user_crud.create_admin_user(db, obj_in=user_in)
        return user
    
    async def get_overview(self, db: AsyncSession) -> dict[str, int]:
        """
        Fetch count of the books, audiobooks, teachings, places, temples, festivals, and stories.
        Returns:
            dict: A dictionary containing the counts of each category.
        """
        overview_data = OverviewResponse(
            books= await book_crud.get_books_count(db=db, content_type="BOOK"), # Assuming db is passed as None for global count
            audiobooks= await book_crud.get_books_count(db=db, content_type="AUDIO"),
            teachings= await teaching_crud.get_teachings_count(db=db),
            places= await place_crud.get_places_count(db=db),
            temples= await temple_crud.get_temples_count(db=db),
            festivals= await festival_crud.get_festivals_count(db=db),
            stories= await story_crud.get_stories_count(db=db),
        )

        return overview_data.model_dump()  # Convert Pydantic model to dict

auth_service = AuthService()