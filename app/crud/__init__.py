# app/crud/__init__.py
from .base import CRUDBase
from .user import user_crud
from .place import place_crud
# ...
from .book import book_crud
from .book_chapter import book_chapter_crud
from .book_section import book_section_crud
from .story import story_crud
from .teaching import teaching_crud
# ...
from .category import category_crud
from .lost_heritage import lost_heritage_crud
from .collection import collection_crud, collection_item_crud
from .temple import temple_crud
from .pilgrimage_route import pilgrimage_route_crud