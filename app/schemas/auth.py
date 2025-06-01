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