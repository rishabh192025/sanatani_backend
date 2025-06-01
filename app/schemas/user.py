# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, LanguageCode # Import your enums

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False
    role: Optional[UserRole] = UserRole.USER
    preferred_language: Optional[LanguageCode] = LanguageCode.EN

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None
    preferred_language: Optional[LanguageCode] = None
    # Do not allow password update here directly, create a separate endpoint for that

class UserResponse(UserBase):
    id: UUID
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    # spiritual_name: Optional[str] = None # Add fields as needed
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replaces orm_mode in Pydantic v2