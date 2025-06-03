# app/api/v1/__init__.py

from fastapi import APIRouter

from . import auth
from . import content
from . import users
from . import place
# api_router_v1 = APIRouter()
# api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# api_router_v1.include_router(content.router, prefix="/content", tags=["Content"])
# api_router_v1.include_router(users.router, prefix="/users", tags=["Users"])

# For now, let main.py handle including individual routers directly
# This file mainly serves to make 'v1' a package.