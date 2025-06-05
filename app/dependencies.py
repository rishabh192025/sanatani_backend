from fastapi import Depends, HTTPException, status, Request # Request might not be needed now
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID as PyUUID # Not directly used in get_current_user but good for other places

from app.config import settings # Ensure CLERK_JWKS_URL is in settings
from app.database import get_async_db
from app.models.user import User, UserRole # Import UserRole if used in other dependencies
from app.crud.user import user_crud

from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer

# This initialization should ideally happen once when the app starts.
# If dependencies.py is imported multiple times, this could re-initialize.
# A common place is in main.py or a dedicated config/setup module.
# For now, having it here will work for Uvicorn's single process dev mode.
if not settings.CLERK_JWKS_URL:
    raise ValueError("CLERK_JWKS_URL must be configured in settings.")
clerk_config = ClerkConfig(jwks_url=settings.CLERK_JWKS_URL) # Or directly use settings.CLERK_JWKS_URL string
clerk_auth_scheme = ClerkHTTPBearer(config=clerk_config) # Renamed for clarity, it's an auth scheme instance

# The user info returned by Clerk
async def get_current_user(
    # The `clerk_auth_scheme` instance is callable and acts as a dependency.
    # It will return the decoded JWT payload (claims) upon successful verification.
    claims: dict = Depends(clerk_auth_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    # The credentials (now named 'claims' for clarity) will have the decoded JWT claims
    # Typically, Clerk user ID is in the "sub" claim
    clerk_user_id: str = claims.get("sub")

    if not clerk_user_id:
        # This case should ideally be caught by ClerkHTTPBearer if 'sub' is missing after verification,
        # but an extra check is fine.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: User ID (sub) not found in claims.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await user_crud.get_user_by_clerk_id(db, clerk_user_id=clerk_user_id)
    if user is None:
        # This indicates the webhook for user creation hasn't synced this user yet,
        # or the user was deleted in Clerk and then in your DB, but an old token is being used.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 is appropriate as they are authenticated by Clerk but not authorized in your app
            detail="User authenticated by Clerk but not found/authorized in this application. Please try again shortly or contact support if the issue persists."
        )
    if not user.is_active: # Check your application's active status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 403
            detail="User account is inactive in this application."
        )

    return user

# Other dependencies like get_current_active_admin remain the same
async def get_current_active_admin(
    #current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Admin access required)"
        )
    return current_user

async def get_current_active_moderator_or_admin(
    #current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Moderator or Admin access required)"
        )
    return current_user