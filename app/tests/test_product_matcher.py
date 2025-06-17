"""
Test the product matching functionality.
"""
import asyncio
import sys
import unittest
from typing import Dict, List

# Add the parent directory to the path so we can import app modules
sys.path.append('/home/justindupre/dev/TCGWallet-API')

from app.models.card import CardData, MatchResult
from app.services import card_matcher


class TestProductMatcher(unittest.TestCase):
    """Test the product matching functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Sample card data
        self.card_data = CardData(
            id="001",
            pack_id="569101",  # OP01 pack ID
            name="Monkey D. Luffy",
            rarity="Secret Rare",
            category="Character",
            img_url="https://example.com/image.jpg",
            img_full_url="https://example.com/image_full.jpg",
            colors=["Red"],
            cost=5,
            attributes=["Strike"],
            power=7000,
            counter=1000,
            types=["Supernovas", "Straw Hat Crew"],
            effect="[DON!!x1] When this card attacks, draw 1 card.",
            trigger=None
        )
        
        # Sample matches
        self.match = MatchResult(
            card=self.card_data,
            score=0.95
        )
        
        # Sample TCGPlayer product data
        self.products = [
            {
                "productId": 12345,
                "name": "Monkey D. Luffy - OP01-001",
                "extendedData": [
                    {"name": "Number", "value": "OP01-001"},
                    {"name": "Rarity", "value": "Secret Rare"},
                    {"name": "Color", "value": "Red"}
                ]
            },
            {
                "productId": 67890,
                "name": "Monkey D. Luffy (Alternate Art) - OP01-001",
                "extendedData": [
                    {"name": "Number", "value": "OP01-001"}, 
                    {"name": "Rarity", "value": "Secret Rare"},
                    {"name": "Color", "value": "Red"}
                ]
            }
        ]
        
        # Sample TCGPlayer price data
        self.prices = [
            {
                "productId": 12345,
                "lowPrice": 100.0,
                "midPrice": 120.0,
                "highPrice": 150.0,
                "marketPrice": 125.0,
                "directLowPrice": None,
                "subTypeName": "Normal"
            },
            {
                "productId": 67890,
                "lowPrice": 200.0,
                "midPrice": 220.0,
                "highPrice": 250.0,
                "marketPrice": 225.0,
                "directLowPrice": None,
                "subTypeName": "Normal"
            }
        ]
    
    def test_find_product_by_card_id(self):
        """Test finding a product by card ID."""
        # Import the function directly from image.py
        from app.api.image import find_product_by_card_id
        
        # Test with exact match
        product = find_product_by_card_id(self.products, "OP01-001")
        self.assertIsNotNone(product)
        self.assertEqual(product["productId"], 12345)
        self.assertEqual(product["name"], "Monkey D. Luffy - OP01-001")
        
        # Test with non-existent card ID
        product = find_product_by_card_id(self.products, "NONEXISTENT-001")
        self.assertIsNone(product)
        
        # Test with empty products list
        product = find_product_by_card_id([], "OP01-001")
        self.assertIsNone(product)
        
        # Test with None products
        product = find_product_by_card_id(None, "OP01-001")
        self.assertIsNone(product)


if __name__ == "__main__":
    unittest.main()
