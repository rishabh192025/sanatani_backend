from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
from uuid import UUID


class SourceType(str, Enum):
    ELEVEN_LABS = "eleven labs"


class ChatWithGurujiCreate(BaseModel):
    chat_id: str
    messages: Optional[List[dict]] = None
    source: Optional[SourceType] = SourceType.ELEVEN_LABS
    is_active: Optional[bool] = True

class ChatWithGurujiUpdate(BaseModel):
    chat_id: Optional[str] = None
    messages: Optional[List[dict]] = None
    source: Optional[SourceType] = None
    is_active: Optional[bool] = True


class ChatWithGurujiResponse(BaseModel):
    id: UUID
    chat_id: str
    messages: Optional[List[dict]] = None
    user_id: Optional[UUID] = None
    source: Optional[SourceType] = None
    title: Optional[str] = None

    is_active: Optional[bool] = True

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True