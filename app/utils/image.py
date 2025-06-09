"""
Image processing utilities for the TCGWallet API.
"""
import base64
import io
from typing import Optional, Tuple

from fastapi import UploadFile
from PIL import Image


from PIL import Image


def compress_image(
    image_bytes: bytes,
    max_size: int = 1024,
    quality: int = 85,
    max_file_size_mb: float = 4.0
) -> bytes:
    """
    Compress an image while maintaining good quality for vision models.
    
    Args:
        image_bytes: Original image bytes
        max_size: Maximum width/height in pixels (default: 1024)
        quality: JPEG compression quality 1-100 (default: 85)
        max_file_size_mb: Maximum file size in MB (default: 4.0)
        
    Returns:
        Compressed image bytes
    """
    # Open the image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary (for JPEG compatibility)
    if image.mode in ('RGBA', 'P'):
        # Create a white background for transparent images
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    
    # Calculate resize dimensions while maintaining aspect ratio
    original_width, original_height = image.size
    if max(original_width, original_height) > max_size:
        if original_width > original_height:
            new_width = max_size
            new_height = int((original_height * max_size) / original_width)
        else:
            new_height = max_size
            new_width = int((original_width * max_size) / original_height)
        
        # Resize with high-quality resampling
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Try different quality settings to meet file size requirements
    max_file_size_bytes = max_file_size_mb * 1024 * 1024
    
    for try_quality in [quality, 80, 75, 70, 65]:
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=try_quality, optimize=True)
        compressed_bytes = output.getvalue()
        
        # If size is acceptable, return the compressed image
        if len(compressed_bytes) <= max_file_size_bytes:
            return compressed_bytes
    
    # If still too large, try with smaller dimensions
    if max(image.size) > 512:
        smaller_size = 512
        if image.width > image.height:
            new_width = smaller_size
            new_height = int((image.height * smaller_size) / image.width)
        else:
            new_height = smaller_size
            new_width = int((image.width * smaller_size) / image.height)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=70, optimize=True)
        return output.getvalue()
    
    # Return the last attempt if all else fails
    return compressed_bytes


async def process_image_upload(
    file: UploadFile,
    allowed_types: Tuple[str, ...] = ("image/jpeg", "image/png"),
    compress: bool = True,
    max_size: int = 1024,
    quality: int = 85
) -> Optional[Tuple[bytes, str, str]]:
    """
    Process an uploaded image file and convert it to a data URL.
    
    Args:
        file: The uploaded file object
        allowed_types: Tuple of allowed MIME types
        compress: Whether to compress the image before encoding
        max_size: Maximum width/height for compression (default: 1024)
        quality: JPEG compression quality 1-100 (default: 85)
        
    Returns:
        Tuple containing (image_bytes, data_url, mime_type) or None if invalid
    """
    # Check if file type is allowed
    mime_type = file.content_type
    if mime_type not in allowed_types:
        return None
        
    # Read the file
    original_image_bytes = await file.read()
    
    # Compress the image if requested
    if compress:
        try:
            image_bytes = compress_image(original_image_bytes, max_size, quality)
            # Update mime type to JPEG since compression converts to JPEG
            mime_type = "image/jpeg"
            print(f"Image compressed: {len(original_image_bytes)} -> {len(image_bytes)} bytes "
                  f"({(1 - len(image_bytes)/len(original_image_bytes))*100:.1f}% reduction)")
        except Exception as e:
            print(f"Image compression failed, using original: {e}")
            image_bytes = original_image_bytes
    else:
        image_bytes = original_image_bytes
    
    # Encode as base64
    image_base64 = base64.b64encode(image_bytes).decode()
    
    # Create data URL
    data_url = f"data:{mime_type};base64,{image_base64}"
    
    return image_bytes, data_url, mime_type
