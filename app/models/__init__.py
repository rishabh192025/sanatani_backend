# app/models/__init__.py
from app.database import Base # Make Base easily importable

# Import all your models here so they are registered with Base.metadata
# and for easier imports elsewhere if needed.
from .user import User
from .category import Category
from .content import Content , ContentChapter, ContentTranslation
# from .content import ContentChapter, ContentTranslation # Add when created
# from .places import SacredPlace, PlaceType # Add when created
# ... import other models as they are created