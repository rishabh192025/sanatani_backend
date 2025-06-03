# app/schemas/homepage.py
from pydantic import BaseModel, Field
from typing import List, Optional

class HomepageCard(BaseModel):
    title: str
    description: str
    icon: str # This would likely map to an icon name the frontend can use
    link: Optional[str] = None # Optional: A direct link for this card
    # You could add other fields like 'type' (e.g., 'category_link', 'feature_link')
    # or 'target_id' (e.g., a specific category slug or feature identifier)

class HomepageCardsResponse(BaseModel):
    cards: List[HomepageCard]