# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None # Store user ID (UUID as string) in token

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Msg(BaseModel):
    message: str

class OverviewResponse(BaseModel):
    books: int = 0
    audiobooks: int = 0 
    teachings: int = 0
    places: int = 0
    temples: int = 0
    festivals: int = 0
    stories: int = 0