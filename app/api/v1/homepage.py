# app/api/v1/homepage.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession # If DB interaction was needed
# from app.dependencies import get_async_db # If DB interaction was needed

from app.schemas.homepage import HomepageCard, HomepageCardsResponse

router = APIRouter()

# Statically defined homepage cards data
# The 'icon' field should correspond to icon identifiers your frontend can map.
# The 'link' field can be a frontend route or a backend API path prefix.
HOMEPAGE_CARDS_DATA = [
    {
        "title": "Sacred Books",
        "description": "Access a collection of spiritual texts and e-books.",
        "icon": "icon-book-open-outline", # Example icon name
        "link": "/content/books" # Example frontend link
    },
    {
        "title": "Audiobooks",
        "description": "Listen to spiritual teachings and sacred texts.",
        "icon": "icon-headphones-outline",
        "link": "/content/audiobooks"
    },
    {
        "title": "Lost Heritage",
        "description": "Discover forgotten temples, ruins, and ancient scriptures.",
        "icon": "icon-map-search-outline", # Could be different from 'lost_heritage'
        "link": "/places/lost-heritage" # Assuming 'places' is a main section
    },
    {
        "title": "Panchang",
        "description": "Hindu calendar with auspicious timings.",
        "icon": "icon-calendar-month-outline",
        "link": "/calendar/panchang"
    },
    {
        "title": "Guruji's Teachings",
        "description": "Articles, videos, and podcasts from Guruji.",
        "icon": "icon-teach-outline", # Or a more specific Guruji icon
        "link": "/content/guruji" # Could be a special category or author
    },
    {
        "title": "Temple Directory",
        "description": "Discover sacred places and important temples.",
        "icon": "icon-temple-hindu-outline",
        "link": "/places/temples"
    },
    {
        "title": "Spiritual Stories",
        "description": "Read and listen to enlightening stories.",
        "icon": "icon-account-voice-outline", # Or a storybook icon
        "link": "/content/stories"
    },
    {
        "title": "Meditation Guides", # Added one based on your schema
        "description": "Guided meditations for peace and clarity.",
        "icon": "icon-meditation",
        "link": "/meditation"
    },
    # Example for dynamic category (if you wanted to mix):
    # {
    #     "title": "Featured Category: Vedas", # This would be dynamic
    #     "description": "Explore the ancient wisdom of the Vedas.",
    #     "icon": "icon-scroll-text-outline",
    #     "link": "/categories/vedas" # Assuming 'vedas' is a slug
    # }
]

@router.get("/cards", response_model=HomepageCardsResponse)
async def get_homepage_features():
    """
    Provides a curated list of main features/categories for the homepage.
    This data is currently static but could be made dynamic in the future.
    """
    # If you need to fetch some of this data from the DB (e.g., actual categories):
    # categories = await category_crud.get_featured_categories(db)
    # dynamic_cards = []
    # for cat in categories:
    #     dynamic_cards.append(HomepageCard(title=cat.name, description=cat.description, icon=cat.icon_url or "default-icon", link=f"/categories/{cat.slug}"))
    # combined_cards = HOMEPAGE_CARDS_DATA + dynamic_cards
    # return HomepageCardsResponse(cards=combined_cards)

    # For now, just returning the static list
    cards = [HomepageCard(**card_data) for card_data in HOMEPAGE_CARDS_DATA]
    return HomepageCardsResponse(cards=cards)