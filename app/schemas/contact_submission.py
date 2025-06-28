# app/schemas/contact_submission.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.contact_submission import ContactStatus # Import the enum

# --- Public Facing Schema ---

class ContactSubmissionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=500)
    message: str = Field(..., min_length=10)

# --- Admin Facing Schemas ---

# A lean schema for showing who resolved the issue
class ResolverInfo(BaseModel):
    id: UUID
    email: EmailStr

class ContactSubmissionResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    subject: str
    message: str
    status: ContactStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_by: Optional[ResolverInfo] = None # Nested response model

    class Config:
        from_attributes = True # Pydantic v2 alias for orm_mode

class ContactSubmissionUpdateAdmin(BaseModel):
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = None