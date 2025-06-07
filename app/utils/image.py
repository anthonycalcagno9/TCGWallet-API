"""
Image processing utilities for the TCGWallet API.
"""
import base64
from typing import Optional, Tuple

from fastapi import UploadFile


async def process_image_upload(
    file: UploadFile,
    allowed_types: Tuple[str, ...] = ("image/jpeg", "image/png"),
) -> Optional[Tuple[bytes, str, str]]:
    """
    Process an uploaded image file and convert it to a data URL.
    
    Args:
        file: The uploaded file object
        allowed_types: Tuple of allowed MIME types
        
    Returns:
        Tuple containing (image_bytes, data_url, mime_type) or None if invalid
    """
    # Check if file type is allowed
    mime_type = file.content_type
    if mime_type not in allowed_types:
        return None
        
    # Read the file
    image_bytes = await file.read()
    
    # Encode as base64
    image_base64 = base64.b64encode(image_bytes).decode()
    
    # Create data URL
    data_url = f"data:{mime_type};base64,{image_base64}"
    
    return image_bytes, data_url, mime_type
