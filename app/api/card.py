"""
Card matching API endpoints.
"""
from typing import Dict, Optional

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.card import CardInfo
from app.services import card_matcher
from app.utils.errors import CARD_NOT_FOUND_ERROR

# Get settings
settings = get_settings()

router = APIRouter()


@router.post("/match-card")
async def match_card(
    card_info: CardInfo, 
    weights: Optional[Dict[str, float]] = None,
    num_results: int = 5,
    min_score: float = 0.3
):
    """
    Match a card against the database using custom weights.
    
    Args:
        card_info: Card information to match
        weights: Custom weights for matching algorithm fields
        num_results: Maximum number of results to return
        min_score: Minimum similarity score threshold
        
    Returns:
        List of matching cards with similarity scores
    """
    # Create a matcher instance with custom weights if provided
    matcher = card_matcher
    if weights:
        matcher = card_matcher.__class__(weights=weights or settings.default_matcher_weights)
    
    matches = matcher.find_best_matches(
        card_info,
        num_results=num_results,
        min_score=min_score
    )
    
    if not matches:
        raise CARD_NOT_FOUND_ERROR
    
    return {
        "matches": [
            {
                "card": match.card,
                "score": match.score
            } for match in matches
        ]
    }
