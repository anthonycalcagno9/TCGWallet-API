"""
TCGPlayer API client service for fetching card data and prices.
"""
from typing import List, Optional

import requests

from app.models.tcgplayer import TCGPlayerGroup, TCGPlayerPrice, TCGPlayerProduct


class TCGPlayerAPI:
    """TCGPlayer API client for fetching card data and prices."""
    
    BASE_URL = "https://tcgcsv.com/tcgplayer"
    CATEGORY_ID = 68  # One Piece Card Game category ID
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the TCGPlayer API client.
        
        Args:
            base_url: Optional custom base URL for the API
        """
        self.base_url = base_url or self.BASE_URL
    
    async def get_groups(self) -> List[TCGPlayerGroup]:
        """Fetch all One Piece card groups (sets/expansions).
        
        Returns:
            List of group objects
        """
        url = f"{self.base_url}/{self.CATEGORY_ID}/groups"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"API Error: Status {response.status_code} - {response.text[:100]}")
                return []
                
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text[:200]}")
            return []
        except Exception as e:
            print(f"Error fetching groups: {type(e).__name__}: {e}")
            return []
    
    async def get_products(self, group_id: Optional[int] = None) -> List[TCGPlayerProduct]:
        """Fetch One Piece card products.
        
        Args:
            group_id: Optional group ID to filter products by set
            
        Returns:
            List of product objects
        """
        # For the products endpoint, we need to use a specific group ID
        if not group_id:
            print("Warning: Products endpoint requires a group ID")
            return []
            
        url = f"{self.base_url}/{self.CATEGORY_ID}/{group_id}/products"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"API Error: Status {response.status_code} - {response.text[:100]}")
                return []
                
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text[:200]}")
            return []
        except Exception as e:
            print(f"Error fetching products: {type(e).__name__}: {e}")
            return []
    
    async def get_prices(self, group_id: int) -> List[TCGPlayerPrice]:
        """Fetch prices for One Piece card products in a specific group/set.
        
        Args:
            group_id: The group ID to fetch prices for
            
        Returns:
            List of product price objects
        """
        url = f"{self.base_url}/{self.CATEGORY_ID}/{group_id}/prices"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"API Error: Status {response.status_code} - {response.text[:100]}")
                return []
                
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text[:200]}")
            return []
        except Exception as e:
            print(f"Error fetching prices: {type(e).__name__}: {e}")
            return []
