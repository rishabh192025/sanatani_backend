from typing import Optional

from pydantic import BaseModel

class PresignRequest(BaseModel):
    filename: Optional[str] = None
    content_type: Optional[str] = None