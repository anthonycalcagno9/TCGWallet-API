"""
Image analysis and card recognition API endpoints.
"""
from fastapi import APIRouter, File, UploadFile
from openai import OpenAI

from app.core.config import get_settings
from app.models.card import CardInfo
from app.services import card_matcher
from app.utils.errors import INVALID_IMAGE_ERROR, MISSING_API_KEY_ERROR
from app.utils.image import process_image_upload

# Initialize settings
settings = get_settings()

router = APIRouter()


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
        
    image_bytes, data_url = image_result
    
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
    
    return {
        "description": card_info,
        "filename": file.filename,
        "size": len(image_bytes),
        "matches": [
            {
                "card": match.card,
                "score": match.score
            } for match in matches
        ]
    }
