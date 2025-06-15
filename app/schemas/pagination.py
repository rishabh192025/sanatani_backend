# app/schemas/pagination.py (New File)
from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic, Optional, Any

DataType = TypeVar('DataType')

class PaginatedResponse(BaseModel, Generic[DataType]):
    total_count: int = Field(..., description="Total number of items matching the query.")
    limit: int = Field(..., description="Number of items returned in this response (page size).")
    skip: int = Field(..., description="Number of items skipped (offset).")
    next_page: Optional[str] = Field(None, description="URL for the next page, if available.")
    prev_page: Optional[str] = Field(None, description="URL for the previous page, if available.")
    items: List[DataType] = Field(..., description="List of items for the current page.")

    class Config:
        from_attributes = True # For Pydantic v2