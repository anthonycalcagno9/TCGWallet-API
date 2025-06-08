"""
Card data models for the TCGWallet API.
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

# Define types for the card fields
Rarity = Literal[
    'Common', 'Uncommon', 'Rare', 'Super Rare', 'Secret Rare', 'Promo', 'DON!!', 'Leader'
]
Color = Literal['Red', 'Blue', 'Green', 'Yellow', 'Black', 'Purple']
Counter = Literal[1000, 2000, 3000]
CardType = Literal['Character', 'Leader', 'Event', 'Stage']
Attribute = Literal['Strike', 'Slash', 'Special', 'Ranged', 'Wisdom']

class CardInfo(BaseModel):
    """Card information model parsed from image analysis."""
    name: Optional[str] = None
    type: Optional[CardType] = None
    cost: Optional[int] = None
    rarity: Optional[Rarity] = None
    color: Optional[Color] = None
    counter: Optional[Counter] = None
    trait: Optional[str] = None
    card_number: Optional[str] = None
    price: Optional[float] = None
    tcgplayer_url: Optional[str] = None
    tcgplayer_product_id: Optional[int] = None

class CardData(BaseModel):
    """Card data model representing complete card data from database or JSON files."""
    id: str
    pack_id: str
    name: str
    rarity: str
    category: str
    img_url: str
    img_full_url: str
    colors: List[Color]
    cost: Optional[int] = None
    attributes: List[str]
    power: Optional[int] = None
    counter: Optional[int] = None
    types: List[str]
    effect: str
    trigger: Optional[str] = None
    
    # Additional fields for matched cards
    score: Optional[float] = None

class MatchResult(BaseModel):
    """Result model for card matching operations."""
    card: CardData
    score: float
    tcgplayer_product_id: Optional[int] = None
    tcgplayer_product: Optional[Dict] = None
    tcgplayer_price: Optional[Dict] = None
