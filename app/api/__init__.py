"""
API router initialization and registration.
"""
from fastapi import APIRouter

from app.api import card, image, tcgplayer

# Create main API router
api_router = APIRouter()

# Include all API routers with their prefixes
api_router.include_router(image.router, prefix="/image", tags=["Image Analysis"])
api_router.include_router(card.router, prefix="/card", tags=["Card Matching"])
api_router.include_router(tcgplayer.router, prefix="/tcgplayer", tags=["TCGPlayer Data"])