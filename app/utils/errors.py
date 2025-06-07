"""
Error handling utilities for the TCGWallet API.
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class APIError(HTTPException):
    """Custom API error with standard format."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or f"ERR_{status_code}"


# Common error instances
INVALID_IMAGE_ERROR = APIError(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Only JPEG and PNG images are supported",
    error_code="INVALID_IMAGE_FORMAT"
)

CARD_NOT_FOUND_ERROR = APIError(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="No matching cards found with the given criteria",
    error_code="CARD_NOT_FOUND"
)

MISSING_API_KEY_ERROR = APIError(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="OpenAI API key not configured",
    error_code="MISSING_API_KEY"
)

GROUP_NOT_FOUND_ERROR = APIError(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="No card groups found",
    error_code="GROUP_NOT_FOUND"
)

def PRODUCTS_NOT_FOUND_ERROR(group_id):
    return APIError(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No products found for group ID {group_id}",
        error_code="PRODUCTS_NOT_FOUND"
    )

def PRICES_NOT_FOUND_ERROR(group_id):
    return APIError(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No prices found for group ID {group_id}",
        error_code="PRICES_NOT_FOUND"
    )
