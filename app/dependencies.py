# app/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID as PyUUID
from jose import JWTError

from app.config import settings
from app.database import get_async_db
from app.models.user import User, UserRole
from app.crud.user import user_crud
from app.utils.security import verify_clerk_jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Get current user by verifying Clerk JWT token
    """
    try:
        # Verify the JWT token and get claims
        # For testing, you can set check_expiration=False to bypass expiration
        claims = await verify_clerk_jwt(credentials.credentials, check_expiration=False)
        # Extract user ID from claims
        clerk_user_id: str = claims.get("sub")
        if not clerk_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: User ID (sub) not found in claims.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        user = await user_crud.get_user_by_clerk_id(db, clerk_user_id=clerk_user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User authenticated by Clerk but not found/authorized in this application. Please try again shortly or contact support if the issue persists."
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive in this application."
            )
        
        return user
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    # Ensure role comparison is correct (string vs enum member)
    if current_user.role != UserRole.ADMIN.value: # Assuming role is stored as string 'ADMIN'
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Admin access required)"
        )
    return current_user

async def get_current_active_moderator_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    # Assuming roles are stored as strings 'ADMIN', 'MODERATOR'
    if current_user.role not in [UserRole.ADMIN.value, UserRole.MODERATOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Moderator or Admin access required)"
        )
    return current_user