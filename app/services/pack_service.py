"""
Pack service for retrieving pack information from packs.json
"""
import json
from typing import Dict, List, Optional

from app.models.card import CardData


class PackService:
    """Service for retrieving pack information from packs.json"""
    
    def __init__(self, packs_file: str = "data/cards_by_pack/packs.json"):
        """Initialize the pack service.
        
        Args:
            packs_file: Path to the packs JSON file
        """
        self.packs_file = packs_file
        self._packs_data = None  # Lazy loaded
        
    @property
    def packs_data(self) -> List[Dict]:
        """
        Lazy load pack data from JSON file.
        """
        if self._packs_data is None:
            try:
                with open(self.packs_file, 'r', encoding='utf-8') as f:
                    self._packs_data = json.load(f)
                print(f"Loaded {len(self._packs_data)} packs from {self.packs_file}")
            except Exception as e:
                print(f"Error loading {self.packs_file}: {e}")
                self._packs_data = []
                
        return self._packs_data
    
    def get_pack_info_by_id(self, pack_id: str) -> Optional[Dict]:
        """
        Get pack information by pack_id.
        
        Args:
            pack_id: The ID of the pack
            
        Returns:
            Dict with pack information or None if not found
        """
        for pack in self.packs_data:
            if pack.get("id") == pack_id:
                return pack
        return None
    
    def get_pack_info_for_card(self, card: CardData) -> Optional[Dict]:
        """
        Get pack information for a card.
        
        Args:
            card: CardData object
            
        Returns:
            Dict with pack information or None if not found
        """
        if not card or not card.pack_id:
            return None
        
        return self.get_pack_info_by_id(card.pack_id)
    
    def get_pack_label(self, pack_id: str) -> Optional[str]:
        """
        Get pack label for a pack.
        
        Args:
            pack_id: The ID of the pack
            
        Returns:
            Pack label (e.g. ST-23, OP-10) or None if not found
        """
        pack_info = self.get_pack_info_by_id(pack_id)
        if pack_info and "title_parts" in pack_info and "label" in pack_info["title_parts"]:
            return pack_info["title_parts"]["label"]
        return None
        
    async def get_tcg_group_id(self, pack_id: str) -> Optional[int]:
        """
        Get TCGPlayer group ID for a pack by matching the abbreviation.
        
        Args:
            pack_id: The ID of the pack
            
        Returns:
            TCGPlayer group ID (integer) or None if not found
        """
        from app.services import tcgplayer_api
        
        # Get the pack label (e.g., ST-23, OP-10)
        pack_label = self.get_pack_label(pack_id)
        if not pack_label:
            return None
        
        # Fetch all groups from TCGPlayer API and find the matching abbreviation
        groups = await tcgplayer_api.get_groups()
        for group in groups:
            if group.get("abbreviation") == pack_label:
                return group.get("groupId")
        
        return None


# Create a singleton instance
pack_service = PackService()
