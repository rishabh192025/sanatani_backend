# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserResponse
from app.config import settings
from app.dependencies import get_current_user, get_current_active_admin # For /me endpoint
from app.models.user import User # For type hinting

router = APIRouter()

@router.get("/admin/me", response_model=UserResponse) # Or just /me if you consolidate
async def read_admin_me( # Renamed for clarity if you keep separate /me
    current_admin: User = Depends(get_current_active_admin) # Uses the new get_current_active_admin
):
    return current_admin