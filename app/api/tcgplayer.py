"""
TCGPlayer card data and price API endpoints.
"""

from fastapi import APIRouter

from app.services import tcgplayer_api
from app.utils.errors import GROUP_NOT_FOUND_ERROR, PRICES_NOT_FOUND_ERROR, PRODUCTS_NOT_FOUND_ERROR

router = APIRouter()


@router.get("/groups")
async def get_card_groups():
    """
    Get all One Piece card groups (sets/expansions).
    """
    groups = await tcgplayer_api.get_groups()
    if not groups:
        raise GROUP_NOT_FOUND_ERROR
    return {"groups": groups}


@router.get("/products/{group_id}")
async def get_products(group_id: int):
    """
    Get all products for a specific card group/set.
    
    Args:
        group_id: The TCGPlayer group ID
    """
    products = await tcgplayer_api.get_products(group_id=group_id)
    if not products:
        raise PRODUCTS_NOT_FOUND_ERROR(group_id)
    return {"products": products}


@router.get("/prices/{group_id}")
async def get_prices(group_id: int):
    """
    Get all prices for a specific card group/set.
    
    Args:
        group_id: The TCGPlayer group ID
    """
    prices = await tcgplayer_api.get_prices(group_id=group_id)
    if not prices:
        raise PRICES_NOT_FOUND_ERROR(group_id)
    return {"prices": prices}
