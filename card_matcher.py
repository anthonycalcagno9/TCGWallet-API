import json
from typing import Dict, List, Optional, Tuple, Any
import glob

# For string similarity comparison
from rapidfuzz import distance as editdistance

# Import models from our models file
from models import CardInfo, CardData, MatchResult

class CardMatcher:
    """
    A class to compare a CardInfo object with card data from JSON files
    and find the closest match using a weighted scoring system.
    """
    
    def __init__(
        self,
        weights: Dict[str, float] = None,
        cards_dir: str = "data/cards_by_pack"
    ):
        """
        Initialize the CardMatcher with configurable weights.
        
        Args:
            weights: Dictionary mapping field names to their weights
            cards_dir: Directory containing the card JSON files
        """
        # Default weights
        self.weights = weights or {
            "id": 7.0,        # Highest weight for card ID/number
            "cost": 5.0,      # Second highest for cost
            "name": 3.0,      # Medium weight for name
            "color": 3.0,     # Medium weight for color
            "counter": 3.0,   # Medium weight for counter
            "category": 2.0,  # Lower weight for category/type
            "rarity": 2.0     # Lower weight for rarity
        }
        
        self.cards_dir = cards_dir
        self._all_cards = None  # Lazy loaded
    
    @property
    def all_cards(self) -> List[CardData]:
        """
        Lazy load all cards from JSON files.
        """
        if self._all_cards is None:
            self._all_cards = []
            
            # Get all card pack JSON files
            card_files = glob.glob(f"{self.cards_dir}/cards_*.json")
            
            # Load cards from each file
            for card_file in card_files:
                try:
                    with open(card_file, 'r', encoding='utf-8') as f:
                        cards_data = json.load(f)
                        # Convert each dict to a CardData object
                        cards = [CardData(**card) for card in cards_data]
                        self._all_cards.extend(cards)
                except Exception as e:
                    print(f"Error loading {card_file}: {e}")
            
            print(f"Loaded {len(self._all_cards)} cards")
            
        return self._all_cards
    
    def _calculate_similarity_score(self, llm_parsed_card_info: CardInfo, card_data: CardData) -> float:
        """
        Calculate a weighted similarity score between a CardInfo object and a CardData object.
        Higher score means better match.
        
        Args:
            card_info: CardInfo object from the image analysis
            card_data: CardData object from JSON
            
        Returns:
            float: Similarity score
        """
        score = 0.0
        max_possible_score = sum(self.weights.values())
        
        # ID/card number matching
        if llm_parsed_card_info.card_number and card_data.id:
            # Normalize both IDs to remove potential formatting differences
            info_id = llm_parsed_card_info.card_number.upper().replace('-', '').replace('_', '')
            data_id = card_data.id.upper().replace('-', '').replace('_', '')
            
            # Exact match
            if info_id == data_id:
                score += self.weights["id"]
            # For partially matching IDs, use Levenshtein distance
            else:
                distance = editdistance.Levenshtein.distance(info_id, data_id)
                max_len = max(len(info_id), len(data_id))
                
                if max_len > 0:
                    similarity = 1.0 - (distance / max_len)
                    
                    # Only consider significant matches
                    if similarity >= 0.7:  # Higher threshold for IDs since they're more specific
                        score += self.weights["id"] * similarity
        
        # Cost matching
        if llm_parsed_card_info.cost is not None and card_data.cost is not None:
            if llm_parsed_card_info.cost == card_data.cost:
                score += self.weights["cost"]
        
        # Name matching
        if llm_parsed_card_info.name and card_data.name:
            # Normalize names
            info_name = llm_parsed_card_info.name.lower().replace('.', '').replace(' ', '')
            data_name = card_data.name.lower().replace('.', '').replace(' ', '')
            
            if info_name == data_name:
                score += self.weights["name"]
            else:
                # Calculate Levenshtein distance
                distance = editdistance.Levenshtein.distance(info_name, data_name)
                
                # Convert to similarity ratio (0-1)
                max_len = max(len(info_name), len(data_name))
                if max_len > 0:  # Avoid division by zero
                    similarity = 1.0 - (distance / max_len)
                    
                    # Only consider matches with similarity above threshold
                    if similarity >= 0.6:  # Adjust threshold as needed
                        score += self.weights["name"] * similarity
        
        # Color matching
        if llm_parsed_card_info.color and card_data.colors:
            # CardInfo has a single color, but JSON has a list of colors
            if llm_parsed_card_info.color in card_data.colors:
                score += self.weights["color"]
            elif card_data.colors and llm_parsed_card_info.color.lower() in [c.lower() for c in card_data.colors]:
                # Case-insensitive match
                score += self.weights["color"] * 0.9
        
        # Counter matching
        if llm_parsed_card_info.counter is not None and card_data.counter is not None:
            if llm_parsed_card_info.counter == card_data.counter:
                score += self.weights["counter"]
            elif card_data.counter is not None:
                # Allow some tolerance for counter value
                counter_diff = abs(llm_parsed_card_info.counter - card_data.counter)
                if counter_diff <= 1000:  # Counters are typically in 1000s
                    score += self.weights["counter"] * (1 - counter_diff / 2000)
        
        # Type/category matching
        if llm_parsed_card_info.type and card_data.category:
            if llm_parsed_card_info.type.lower() == card_data.category.lower():
                score += self.weights["category"]
        
        # Rarity matching
        if llm_parsed_card_info.rarity and card_data.rarity:
            # Map abbreviated rarities to full names
            rarity_map = {
                "C": "Common",
                "UC": "Uncommon", 
                "R": "Rare",
                "SR": "SuperRare",
                "SEC": "SecretRare",
                "P": "Promo",
                "L": "Leader",
                "DON": "DON!!"
            }
            
            info_rarity = rarity_map.get(llm_parsed_card_info.rarity, llm_parsed_card_info.rarity)
            
            if info_rarity.lower().replace(' ', '') == card_data.rarity.lower().replace(' ', ''):
                score += self.weights["rarity"]
        
        # Normalize score to 0-1 range
        return score / max_possible_score
    
    def find_best_matches(
        self, 
        llm_parsed_card_info: CardInfo, 
        num_results: int = 5,
        min_score: float = 0.3
    ) -> List[MatchResult]:
        """
        Find the best matching cards for a given CardInfo.
        
        Args:
            card_info: CardInfo object from the image analysis
            num_results: Maximum number of results to return
            min_score: Minimum similarity score to include in results
            
        Returns:
            List of MatchResult objects containing matched card data and score
        """
        matches = []
        
        for card_data in self.all_cards:
            score = self._calculate_similarity_score(llm_parsed_card_info, card_data)
            if score >= min_score:
                # Create a copy of the card data with the score
                card_with_score = card_data.model_copy(update={"score": score})
                matches.append(MatchResult(card=card_with_score, score=score))
        
        # Sort by score in descending order
        matches.sort(key=lambda x: x.score, reverse=True)
        
        return matches[:num_results]
    
    def find_best_match(self, llm_parsed_card_info: CardInfo) -> Optional[MatchResult]:
        """
        Find the single best matching card for a given CardInfo.
        
        Args:
            card_info: CardInfo object from the image analysis
            
        Returns:
            MatchResult object with the best match or None if no match found
        """
        matches = self.find_best_matches(llm_parsed_card_info, num_results=1, min_score=0.0)
        if matches:
            return matches[0]
        return None
