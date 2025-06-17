"""
Models initialization file.
Import all models here to make them available from the models package.
"""
from app.models.card import (
    Attribute,
    CardData,
    CardInfo,
    CardType,
    Color,
    Counter,
    MatchResult,
    Rarity,
)
from app.models.tcgplayer import (
    TCGPlayerGroup,
    TCGPlayerGroupResponse,
    TCGPlayerPrice,
    TCGPlayerPriceResponse,
    TCGPlayerProduct,
    TCGPlayerProductResponse,
)

__all__ = [
    "Attribute",
    "CardData",
    "CardInfo", 
    "CardType",
    "Color",
    "Counter",
    "MatchResult",
    "Rarity",
    "TCGPlayerGroup",
    "TCGPlayerGroupResponse",
    "TCGPlayerPrice",
    "TCGPlayerPriceResponse",
    "TCGPlayerProduct",
    "TCGPlayerProductResponse",
]

# For easy testing, provide a mock card
mock_card = CardInfo(
    name='Monkey.D.Luffy',
    type='Character',
    cost=6,
    rarity='Promo',
    colors=['Red'],
    counter=None,
    trait='Supernovas/Straw Hat Crew',
    card_number='P-001',
)