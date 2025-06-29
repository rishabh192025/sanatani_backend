# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import Token, UserLogin, Msg, OverviewResponse
from app.schemas.user import UserCreate, UserResponse, AdminCreate
from app.dependencies import get_async_db
from app.services.auth_service import auth_service
from app.config import settings
from app.utils.security import create_access_token
from jose import jwt, JWTError
from app.crud.user import user_crud
from app.dependencies import get_current_user, get_current_active_admin
from app.models.user import User

router = APIRouter()

@router.post("/admin/login", response_model=Token)
async def login_for_access_token(
    login_data: UserLogin, # Use Pydantic model for JSON body
    db: AsyncSession = Depends(get_async_db)
):
    user = await auth_service.authenticate_admin_user(db, login_data=login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token, refresh_token = auth_service.generate_tokens(user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# @router.post("/admin/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def register_user(
#     user_in: AdminCreate, 
#     db: AsyncSession = Depends(get_async_db)
# ):
#     user = await auth_service.register_new_admin_user(db=db, user_in=user_in)
#     # Optionally, log in the user immediately and return tokens
#     return user


@router.post("/admin/refresh-token", response_model=Token)
async def refresh_access_token(
    refresh_token_str: str, # Expecting refresh token in body or header
    db: AsyncSession = Depends(get_async_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True} # Ensure token isn't expired
        )
        if payload.get("token_type") != "refresh":
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        user = await user_crud.get_user(db, user_id=user_id) # Fetch user to ensure they still exist/active
        if not user or not user.is_active:
            raise credentials_exception
            
        new_access_token = create_access_token(data={"sub": user_id})
        # Optionally, issue a new refresh token as well for sliding sessions
        # new_refresh_token = create_refresh_token(data={"sub": user_id})

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token_str, # or new_refresh_token
            "token_type": "bearer"
        }
    except JWTError:
        raise credentials_exception

@router.get("/admin/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_admin)
    ):
    """
    Get current logged-in user.
    """
    return current_user

@router.get("/admin/overview", response_model=OverviewResponse)
async def read_overview(
    #current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get overview of the books, audiobooks, teachings, places, temples, festivals, and stories.
    This endpoint is for admin users to get a quick overview of the system.
    """
    overview = await auth_service.get_overview(db=db)
    if not overview:
        raise HTTPException(status_code=404, detail="Overview not found")
    
    return overview

