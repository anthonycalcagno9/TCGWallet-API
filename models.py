"""
Shared models for the TCGWallet API.
"""
from typing import Optional, Literal, List, Dict, Any, Union
from pydantic import BaseModel

# Define types for the card fields
Rarity = Literal['Common', 'Uncommon', 'Rare', 'Super Rare', 'Secret Rare', 'Promo', 'DON!!', 'Leader']
Color = Literal['Red', 'Blue', 'Green', 'Yellow', 'Black', 'Purple']
Counter = Literal[1000, 2000, 3000]
CardType = Literal['Character', 'Leader', 'Event', 'Stage']
Attribute = Literal['Strike', 'Slash', 'Special', 'Ranged', 'Wisdom']

class CardInfo(BaseModel):
    """Card information model shared between modules."""
    name: Optional[str] = None
    type: Optional[CardType] = None
    cost: Optional[int] = None
    rarity: Optional[Rarity] = None
    color: Optional[Color] = None
    counter: Optional[Counter] = None
    trait: Optional[str] = None
    card_number: Optional[str] = None

class CardData(BaseModel):
    """Card data model representing card data from JSON files."""
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

# Example card for testing
mock_card = CardInfo(
    name='Monkey.D.Luffy',
    type='Character',
    cost=6,
    rarity='Promo',
    color='Red',
    counter=None,
    trait='Supernovas/Straw Hat Crew',
    card_number='P-001',
)
