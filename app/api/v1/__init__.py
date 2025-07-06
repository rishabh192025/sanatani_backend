# app/api/v1/__init__.py

from fastapi import APIRouter

from . import auth
from . import users
from . import homepage
from . import book
from . import temple
from . import place
from . import lost_heritage
from . import location
from . import webhooks
from . import categories
from . import stories
from . import teachings
from . import s3_upload
from . import collections

from . import pilgrimage_route

from . import festivals
from . import contact
from . import chat_with_guruji

# api_router_v1 = APIRouter()
# api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# api_router_v1.include_router(content.router, prefix="/content", tags=["Content"])
# api_router_v1.include_router(users.router, prefix="/users", tags=["Users"])

# For now, let main.py handle including individual routers directly
# This file mainly serves to make 'v1' a package.