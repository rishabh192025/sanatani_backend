# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserLogin, OverviewResponse
from app.services.auth_service import AuthService
from app.database import get_async_db
from app.schemas.user import UserResponse
from app.config import settings
from app.dependencies import get_current_user, get_current_active_admin
from app.models.user import User

router = APIRouter()
auth_service = AuthService()
@router.get("/admin/me", response_model=UserResponse)
async def read_admin_me(
    current_admin: User = Depends(get_current_active_admin)
):

    return current_admin

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