"""
Services initialization file.
Import and initialize service instances here to make them available across the application.
"""
from app.services.card_matcher import CardMatcher
from app.services.pack_service import PackService
from app.services.tcgplayer_api import TCGPlayerAPI

# Create default instances for easy importing
card_matcher = CardMatcher()
tcgplayer_api = TCGPlayerAPI()
pack_service = PackService()