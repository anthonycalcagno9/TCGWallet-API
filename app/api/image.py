"""
Image analysis and card recognition API endpoints.
"""
import asyncio
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, File, UploadFile
from openai import OpenAI

from app.core.config import get_settings
from app.models.card import CardInfo
from app.models.tcgplayer import TCGPlayerProduct
from app.services import card_matcher, pack_service, tcgplayer_api
from app.utils.errors import INVALID_IMAGE_ERROR, MISSING_API_KEY_ERROR
from app.utils.image import process_image_upload

# Initialize settings
settings = get_settings()

router = APIRouter()


def find_product_by_card_id(
    products: List[TCGPlayerProduct], 
    card_id: str, 
    user_image_path: Optional[str] = None
) -> Optional[TCGPlayerProduct]:
    """
    Find a TCGPlayer product by matching the card's ID with the "Number" field in extended data.
    Enhanced to handle parallel cards using image comparison against TCGPlayer product images.
    
    Args:
        products: List of TCGPlayer products
        card_id: The card ID to match (e.g., "OP01-001" or "OP01-001_p1")
        user_image_path: Path to the user's uploaded image to compare against TCGPlayer images
        
    Returns:
        The matching TCGPlayer product or None if not found
    """
    # Start timing for entire product search
    product_search_start_time = time.time()
    
    if not products or not card_id:
        return None
    
    # Check if this is a parallel card (contains _p)
    is_parallel_card = "_p" in card_id
    base_card_id = card_id.split("_p")[0] if is_parallel_card else card_id
    
    # Time the database product matching
    db_match_start_time = time.time()
    
    # First, try to find products that match the base card number
    matching_products = []
    for product in products:
        # Skip products without extended data
        if not product.get("extendedData"):
            continue
        
        # Look for a "Number" field in extended data that matches our base card ID
        for data in product.get("extendedData", []):
            if data.get("name") == "Number" and data.get("value") == base_card_id:
                matching_products.append(product)
                break
    
    db_match_duration = time.time() - db_match_start_time
    print(f"[BENCHMARK] Database product matching took {db_match_duration:.4f}s, "
          f"found {len(matching_products)} matches")
    
    if not matching_products:
        print(f"No product match found for card ID: {card_id}")
        return None
    
    # If we only have one matching product, return it
    if len(matching_products) == 1:
        selected_product = matching_products[0]
        total_duration = time.time() - product_search_start_time
        print(f"[BENCHMARK] Single product match completed in {total_duration:.4f}s")
        print(f"Found single product match: {selected_product.get('name')} "
              f"with ID {selected_product.get('productId')} for card {card_id}")
        return selected_product
    
    # If we have multiple matching products and a user image, use image comparison
    if user_image_path and len(matching_products) > 1:
        from app.utils.image_compare import calculate_image_similarity
        
        print(f"Found {len(matching_products)} products for {card_id}, using image comparison...")
        
        # Time the image comparison process
        image_comparison_start_time = time.time()
        
        best_product = None
        best_similarity = 0.0
        successful_comparisons = 0
        failed_comparisons = 0
        
        for product in matching_products:
            tcg_image_url = product.get("imageUrl")
            if not tcg_image_url:
                continue
                
            # Time individual image comparison
            single_comparison_start_time = time.time()
            
            try:
                similarity = calculate_image_similarity(user_image_path, tcg_image_url)
                single_comparison_duration = time.time() - single_comparison_start_time
                successful_comparisons += 1
                print(f"[BENCHMARK] Image comparison for {product.get('name')} "
                      f"took {single_comparison_duration:.4f}s, similarity: {similarity:.4f}")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_product = product
                    
            except Exception as e:
                single_comparison_duration = time.time() - single_comparison_start_time
                failed_comparisons += 1
                print(f"[BENCHMARK] Failed image comparison for product "
                      f"{product.get('productId')} took {single_comparison_duration:.4f}s: {e}")
                continue
        
        image_comparison_duration = time.time() - image_comparison_start_time
        print(f"[BENCHMARK] Total image comparison took {image_comparison_duration:.4f}s")
        print(f"[BENCHMARK] Image comparisons: {successful_comparisons} successful, "
              f"{failed_comparisons} failed")
        
        if best_product and best_similarity > 0.3:  # Minimum similarity threshold
            total_duration = time.time() - product_search_start_time
            print(f"[BENCHMARK] Product search with image comparison "
                  f"completed in {total_duration:.4f}s")
            print(f"Best image match: {best_product.get('name')} "
                  f"with similarity {best_similarity:.4f}")
            return best_product
        else:
            print(f"No good image matches found (best: {best_similarity:.4f}), "
                  f"falling back to text-based selection")
    
    # Time the text-based fallback selection
    text_fallback_start_time = time.time()
    
    # Fallback to text-based selection for parallel cards
    if is_parallel_card:
        # Look for parallel version first (products with "Parallel" in name)
        for product in matching_products:
            product_name = product.get("name", "").lower()
            if "parallel" in product_name:
                text_fallback_duration = time.time() - text_fallback_start_time
                total_duration = time.time() - product_search_start_time
                print(f"[BENCHMARK] Text-based parallel matching "
                      f"took {text_fallback_duration:.4f}s")
                print(f"[BENCHMARK] Total product search took {total_duration:.4f}s")
                print(f"Found parallel product match: {product.get('name')} "
                      f"with ID {product.get('productId')} for parallel card {card_id}")
                return product
        
        # If no parallel version found, fall back to the first regular version
        print(f"No parallel version found for {card_id}, falling back to regular version")
    
    # Return the first matching product (either regular card or fallback for parallel)
    selected_product = matching_products[0]
    text_fallback_duration = time.time() - text_fallback_start_time
    total_duration = time.time() - product_search_start_time
    print(f"[BENCHMARK] Text-based fallback took {text_fallback_duration:.4f}s")
    print(f"[BENCHMARK] Total product search took {total_duration:.4f}s")
    print(f"Found product match: {selected_product.get('name')} "
          f"with ID {selected_product.get('productId')} for card {card_id}")
    return selected_product


async def fetch_tcgplayer_data(pack_id: str) -> Dict:
    """
    Fetch TCGPlayer product and pricing data for a card's pack.
    
    Args:
        pack_id: The pack ID from the card
        
    Returns:
        Dictionary with tcgplayer_group_id, products, and prices
    """
    # Time the entire TCGPlayer data fetch process
    tcg_fetch_start_time = time.time()
    
    if not pack_id:
        return {
            "tcgplayer_group_id": None,
            "products": [],
            "prices": []
        }
    
    # Time the group ID lookup
    group_id_start_time = time.time()
    group_id = await pack_service.get_tcg_group_id(pack_id)
    group_id_duration = time.time() - group_id_start_time
    print(f"[BENCHMARK] TCGPlayer group ID lookup took {group_id_duration:.4f}s")
    print(f"Fetched TCGPlayer group ID: {group_id} for pack ID: {pack_id}")
    
    if not group_id:
        total_duration = time.time() - tcg_fetch_start_time
        print(f"[BENCHMARK] TCGPlayer data fetch completed in "
              f"{total_duration:.4f}s (no group ID found)")
        return {
            "tcgplayer_group_id": None,
            "products": [],
            "prices": []
        }
    
    # Time the parallel API calls
    api_calls_start_time = time.time()
    
    # Fetch products and prices in parallel
    products_task = asyncio.create_task(tcgplayer_api.get_products(group_id=group_id))
    prices_task = asyncio.create_task(tcgplayer_api.get_prices(group_id=group_id))
    
    # Wait for both tasks to complete
    products, prices = await asyncio.gather(products_task, prices_task)
    
    api_calls_duration = time.time() - api_calls_start_time
    print(f"[BENCHMARK] Parallel TCGPlayer API calls took {api_calls_duration:.4f}s")
    print(f"[BENCHMARK] Retrieved {len(products) if products else 0} products "
          f"and {len(prices) if prices else 0} prices")
    
    # Get the pack label (abbreviation) for reference
    pack_label = pack_service.get_pack_label(pack_id)
    
    total_duration = time.time() - tcg_fetch_start_time
    print(f"[BENCHMARK] Total TCGPlayer data fetch took {total_duration:.4f}s")
    
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
    # Time the entire image analysis process
    total_analysis_start_time = time.time()
    print(f"[BENCHMARK] Starting image analysis for file: {file.filename}")
    
    # Time image processing
    image_processing_start_time = time.time()
    
    # Process the uploaded image with compression enabled
    image_result = await process_image_upload(
        file, 
        compress=settings.compress_images,
        max_size=settings.image_max_size,
        quality=settings.image_quality
    )
    if not image_result:
        raise INVALID_IMAGE_ERROR
        
    image_bytes, data_url, mime_type = image_result
    
    # Save image bytes for later comparison
    temp_image_path = f"/tmp/uploaded_card_{file.filename}"
    with open(temp_image_path, "wb") as f:
        f.write(image_bytes)
    
    image_processing_duration = time.time() - image_processing_start_time
    print(f"[BENCHMARK] Image processing took {image_processing_duration:.4f}s")
    
    # Check if API key is configured
    if not settings.openai_api_key:
        raise MISSING_API_KEY_ERROR
    
    # Time the LLM call
    llm_start_time = time.time()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Send image to OpenAI GPT-4o for analysis using image_url
    response = client.responses.parse(
        model="o4-mini",
        input=[
            {"role": "system", "content": "You are a helpful assistant that describes images."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analyze this image and get the details from the card."
                    },
                    {"type": "input_image", "image_url": data_url}
                ]
            }
        ],
        text_format=CardInfo,
    )
    card_info = response.output_parsed
    
    llm_duration = time.time() - llm_start_time
    print(f"[BENCHMARK] LLM analysis took {llm_duration:.4f}s")
    print(f"[BENCHMARK] Extracted card: {card_info.name if card_info else 'None'}")
    
    # Add the image path to the card info for comparison
    card_info.image_path = temp_image_path
    
    # Time database card matching
    db_matching_start_time = time.time()
    
    # Find matching cards in our database - only get the top match
    matches = card_matcher.find_best_matches(card_info, num_results=1)
    
    db_matching_duration = time.time() - db_matching_start_time
    print(f"[BENCHMARK] Database card matching took {db_matching_duration:.4f}s, "
          f"found {len(matches)} matches")
    
    # For the best match, get TCGPlayer data
    tcgplayer_data = None
    
    if matches and matches[0]:
        best_match = matches[0]
        print(f"[BENCHMARK] Best match: {best_match.card.name} (score: {best_match.score:.4f})")
        
        # Time TCGPlayer data fetching and processing
        tcgplayer_processing_start_time = time.time()
        
        tcgplayer_data = await fetch_tcgplayer_data(best_match.card.pack_id)
        
        # Only process the best match (first one) because other matches 
        # might be from different packs
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
            
            # Find the matching product using image comparison
            matching_product = None
            for possible_id in possible_card_ids:
                matching_product = find_product_by_card_id(
                    tcgplayer_data.get("products"), 
                    possible_id,
                    card_info.image_path  # Pass user's uploaded image for comparison
                )
                if matching_product:
                    break
            
            # Time price matching
            price_matching_start_time = time.time()
            
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
            
            price_matching_duration = time.time() - price_matching_start_time
            print(f"[BENCHMARK] Price matching took {price_matching_duration:.4f}s")
        
        tcgplayer_processing_duration = time.time() - tcgplayer_processing_start_time
        print(f"[BENCHMARK] Total TCGPlayer processing took {tcgplayer_processing_duration:.4f}s")
    
    # Calculate total time and log summary
    total_analysis_duration = time.time() - total_analysis_start_time
    print(f"[BENCHMARK] ==> TOTAL IMAGE ANALYSIS COMPLETED IN {total_analysis_duration:.4f}s")
    tcg_duration = (tcgplayer_processing_duration 
                    if 'tcgplayer_processing_duration' in locals() else 0)
    print(f"[BENCHMARK] Breakdown: Image({image_processing_duration:.4f}s) + "
          f"LLM({llm_duration:.4f}s) + DB({db_matching_duration:.4f}s) + "
          f"TCG({tcg_duration:.4f}s)")
    
    return {
        "description": card_info,
        "filename": file.filename,
        "size": len(image_bytes),
        "benchmark": {
            "total_duration": total_analysis_duration,
            "image_processing_duration": image_processing_duration,
            "llm_duration": llm_duration,
            "database_matching_duration": db_matching_duration,
            "tcgplayer_processing_duration": (
                tcgplayer_processing_duration 
                if 'tcgplayer_processing_duration' in locals() 
                else 0
            )
        },
        "best_match": {
            "card": matches[0].card,
            "score": matches[0].score,
            "tcgplayer_product_id": matches[0].tcgplayer_product_id,
            "tcgplayer_price": (
                matches[0].tcgplayer_price['marketPrice'] 
                if matches[0].tcgplayer_price 
                else None
            )
        } if matches else None,
        "matches": [
            {
                "card": match.card,
                "score": match.score,
                "tcgplayer_product_id": match.tcgplayer_product_id,
                "tcgplayer_price": (
                    match.tcgplayer_price['marketPrice'] 
                    if match.tcgplayer_price 
                    else None
                )
            } for match in matches
        ]
    }
