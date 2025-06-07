"""
Core configuration settings for the application.
"""
import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings and configuration."""
    
    # API Settings
    api_title: str = "TCGWallet API"
    api_description: str = "API for TCG card recognition and pricing"
    api_version: str = "0.1.0"
    
    # Data Directories
    cards_data_dir: str = os.getenv("CARDS_DATA_DIR", "data/cards_by_pack")
    
    # External Services
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Matcher Settings
    default_matcher_weights: dict = {
        "id": 7.0,
        "cost": 5.0,
        "name": 3.0,
        "color": 3.0,
        "counter": 3.0,
        "category": 2.0,
        "rarity": 2.0
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings, cached for performance.
    
    Returns:
        Application settings object
    """
    return Settings()
