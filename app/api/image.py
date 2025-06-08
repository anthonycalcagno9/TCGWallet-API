"""
Image analysis and card recognition API endpoints.
"""
import asyncio
from typing import Dict, List, Optional

from fastapi import APIRouter, File, UploadFile
from openai import OpenAI

from app.core.config import get_settings
from app.models.card import CardInfo
from app.models.tcgplayer import TCGPlayerPrice, TCGPlayerProduct
from app.services import card_matcher, pack_service, tcgplayer_api
from app.utils.errors import INVALID_IMAGE_ERROR, MISSING_API_KEY_ERROR
from app.utils.image import process_image_upload

# Initialize settings
settings = get_settings()

router = APIRouter()


def find_product_by_card_id(products: List[TCGPlayerProduct], card_id: str) -> Optional[TCGPlayerProduct]:
    """
    Find a TCGPlayer product by matching the card's ID with the "Number" field in extended data.
    
    Args:
        products: List of TCGPlayer products
        card_id: The card ID to match (e.g., "OP01-001")
        
    Returns:
        The matching TCGPlayer product or None if not found
    """
    if not products or not card_id:
        return None
    
    for product in products:
        # Skip products without extended data
        if not product.get("extendedData"):
            continue
        
        # Look for a "Number" field in extended data that matches our card ID
        for data in product.get("extendedData", []):
            if data.get("name") == "Number" and data.get("value") == card_id:
                print(f"Found product match: {product.get('name')} with ID {product.get('productId')} for card {card_id}")
                return product
    
    print(f"No product match found for card ID: {card_id}")
    return None


async def fetch_tcgplayer_data(pack_id: str) -> Dict:
    """
    Fetch TCGPlayer product and pricing data for a card's pack.
    
    Args:
        pack_id: The pack ID from the card
        
    Returns:
        Dictionary with tcgplayer_group_id, products, and prices
    """
    if not pack_id:
        return {
            "tcgplayer_group_id": None,
            "products": [],
            "prices": []
        }
    
    # Get the TCGPlayer group ID from the pack service
    group_id = await pack_service.get_tcg_group_id(pack_id)
    print(f"Fetched TCGPlayer group ID: {group_id} for pack ID: {pack_id}")
    
    if not group_id:
        return {
            "tcgplayer_group_id": None,
            "products": [],
            "prices": []
        }
    
    # Fetch products and prices in parallel
    products_task = asyncio.create_task(tcgplayer_api.get_products(group_id=group_id))
    prices_task = asyncio.create_task(tcgplayer_api.get_prices(group_id=group_id))
    
    # Wait for both tasks to complete
    products, prices = await asyncio.gather(products_task, prices_task)
    
    # Get the pack label (abbreviation) for reference
    pack_label = pack_service.get_pack_label(pack_id)
    
    return {
        "tcgplayer_group_id": group_id,
        "tcgplayer_group_label": pack_label,
        "products": products,
        "prices": prices
    }

@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze an image of a card and extract its information using AI.
    
    Args:
        file: The uploaded card image file
        
    Returns:
        Extracted card information and analysis results
    """
    # Process the uploaded image
    image_result = await process_image_upload(file)
    if not image_result:
        raise INVALID_IMAGE_ERROR
        
    image_bytes, data_url, mime_type = image_result
    
    # Check if API key is configured
    if not settings.openai_api_key:
        raise MISSING_API_KEY_ERROR
        
    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Send image to OpenAI GPT-4o for analysis using image_url
    response = client.responses.parse(
        model="gpt-4o",
        tools= [ { "type": "web_search_preview"} ],
        input=[
            {"role": "system", "content": "You are a helpful assistant that describes images."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analyze this image and get the details from the card. "
                               "Then search the internet by searching 'tcgplayer {card name} "
                               "{card number}'. Make sure you find the correct card because "
                               "there are many cards that have the same name. "
                    },
                    {"type": "input_image", "image_url": data_url}
                ]
            }
        ],
        text_format=CardInfo,
    )
    card_info = response.output_parsed
    
    # Find matching cards in our database
    matches = card_matcher.find_best_matches(card_info, num_results=3)
    
    # For the best match, get TCGPlayer data
    tcgplayer_data = None
    
    if matches and matches[0]:
        best_match = matches[0]
        tcgplayer_data = await fetch_tcgplayer_data(best_match.card.pack_id)
        
        # Only process the best match (first one) because other matches might be from different packs
        if tcgplayer_data and tcgplayer_data.get("products"):
            # Get the pack label for creating the full card ID
            pack_label = tcgplayer_data.get("tcgplayer_group_label")
            card_id = best_match.card.id
            
            # Try different formats for the card ID
            possible_card_ids = [
                f"{pack_label}-{card_id}",  # e.g., "OP01-001"
                f"{pack_label}{card_id}",   # e.g., "OP01001"
                card_id                     # Just the card number
            ]
            
            print(f"Trying to match card with IDs: {possible_card_ids}")
            
            # Find the matching product
            matching_product = None
            for possible_id in possible_card_ids:
                matching_product = find_product_by_card_id(
                    tcgplayer_data.get("products"), 
                    possible_id
                )
                if matching_product:
                    break
            
            # If we found a matching product, find its price
            matching_price = None
            if matching_product:
                product_id = matching_product.get("productId")
                for price in tcgplayer_data.get("prices", []):
                    if price.get("productId") == product_id:
                        matching_price = price
                        break
                
                # Update only the best match with TCGPlayer info
                best_match.tcgplayer_product_id = product_id
                best_match.tcgplayer_product = matching_product
                best_match.tcgplayer_price = matching_price
    
    return {
        "description": card_info,
        "filename": file.filename,
        "size": len(image_bytes),
        "matches": [
            {
                "card": match.card,
                "score": match.score,
                "tcgplayer_product_id": match.tcgplayer_product_id,
                "tcgplayer_price": match.tcgplayer_price['marketPrice'] if match.tcgplayer_price else None
            } for match in matches
        ]
    }
