from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class SourceType(str, Enum):
    ELEVEN_LABS = "eleven_labs"


class ChatWithGurujiCreate(BaseModel):
    chat_id: str
    messages: Optional[List[dict]] = None
    source: Optional[SourceType] = SourceType.ELEVEN_LABS
    title: Optional[str] = None  # Optional title for the chat

class ChatWithGurujiUpdate(BaseModel):
    chat_id: Optional[str] = None
    messages: Optional[List[dict]] = None
    source: Optional[SourceType] = None


class ChatWithGurujiResponse(BaseModel):
    id: UUID
    chat_id: str
    messages: Optional[List[dict]] = None
    user_id: Optional[UUID] = None
    source: Optional[SourceType] = None
    title: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True