"""
Card matching service for comparing a CardInfo object with card data from JSON files
and finding the closest match using a weighted scoring system.
"""
import glob
import json
from typing import Dict, List, Optional

# Import models
from rapidfuzz import distance as editdistance

from app.models.card import CardData, CardInfo, MatchResult
from app.utils.image_compare import calculate_image_similarity


class CardMatcher:
    """
    A class to compare a CardInfo object with card data from JSON files
    and find the closest match using a weighted scoring system.
    """
    
    def __init__(
        self,
        weights: Dict[str, float] = None,
        cards_dir: str = "data/cards_by_pack",
        image_weight: float = 8.0  # High weight for image similarity
    ):
        """
        Initialize the CardMatcher with configurable weights.
        
        Args:
            weights: Dictionary mapping field names to their weights
            cards_dir: Directory containing the card JSON files
            image_weight: Weight for image similarity score
        """
        # Default weights
        self.weights = weights or {
            "name": 9.0,   
            "id": 7.0,    
            "cost": 5.0,      
            "color": 3.0,   
            "counter": 3.0,   
            "category": 2.0,  
            "rarity": 2.0     
        }
        
        self.cards_dir = cards_dir
        self._all_cards = None  # Lazy loaded
        self.image_weight = image_weight
    
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
    
    def _calculate_metadata_similarity_score(
        self, llm_parsed_card_info: CardInfo, card_data: CardData
    ) -> float:
        """
        Calculate a weighted similarity score based on metadata only (no image comparison).
        Higher score means better match.
        
        Args:
            llm_parsed_card_info: CardInfo object from the image analysis
            card_data: CardData object from JSON
            
        Returns:
            float: Similarity score (0-1 range)
        """
        score = 0.0
        max_possible_score = sum(self.weights.values())
        
        # ID/card number matching - enhanced for parallel cards
        if llm_parsed_card_info.card_number and card_data.id:
            # Extract base card IDs (remove parallel suffixes like _p1, _p2, etc.)
            def extract_base_id(card_id: str) -> str:
                """Extract base card ID by removing parallel suffixes"""
                return card_id.split('_p')[0] if '_p' in card_id else card_id
            
            info_base_id = extract_base_id(llm_parsed_card_info.card_number)
            data_base_id = extract_base_id(card_data.id)
            
            # Check for base ID match (handles parallel cards)
            if info_base_id.upper().replace('-', '') == data_base_id.upper().replace('-', ''):
                # Exact base match gets full score
                score += self.weights["id"]
            else:
                # Normalize both IDs to remove potential formatting differences
                info_id = llm_parsed_card_info.card_number.upper().replace('-', '').replace('_', '')
                data_id = card_data.id.upper().replace('-', '').replace('_', '')
                
                # Exact full match
                if info_id == data_id:
                    score += self.weights["id"]
                # For partially matching IDs, use Levenshtein distance
                else:
                    distance = editdistance.Levenshtein.distance(info_id, data_id)
                    max_len = max(len(info_id), len(data_id))
                    
                    if max_len > 0:
                        similarity = 1.0 - (distance / max_len)
                        
                        # Only consider significant matches
                        # Higher threshold for IDs since they're more specific
                        if similarity >= 0.7:
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
        if llm_parsed_card_info.colors and card_data.colors:
            # CardInfo now has a list of colors, and JSON also has a list of colors
            # Check if there's any overlap between the two lists
            card_info_colors = [c.lower() for c in llm_parsed_card_info.colors]
            card_data_colors = [c.lower() for c in card_data.colors]
            
            # Check for exact matches first
            exact_matches = set(card_info_colors) & set(card_data_colors)
            if exact_matches:
                score += self.weights["color"]
            else:
                # Check for partial matches (case-insensitive)
                partial_matches = any(
                    info_color in card_data_colors for info_color in card_info_colors
                )
                if partial_matches:
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
            if llm_parsed_card_info.rarity.lower().replace(' ', '') == card_data.rarity.lower().replace(' ', ''):
                score += self.weights["rarity"]
        
        # Normalize score to 0-1 range
        return score / max_possible_score
    
    def _calculate_image_similarity_score(
        self, llm_parsed_card_info: CardInfo, card_data: CardData
    ) -> float:
        """
        Calculate image similarity score between CardInfo and CardData.
        
        Args:
            llm_parsed_card_info: CardInfo object from the image analysis
            card_data: CardData object from JSON
            
        Returns:
            float: Image similarity score (0-1 range), or 0.0 if comparison fails
        """ 
        if not llm_parsed_card_info.image_path or not card_data.img_full_url:
            return 0.0
            
        try:
            return calculate_image_similarity(
                llm_parsed_card_info.image_path, card_data.img_full_url
            )
        except Exception as e:
            print(f"Error comparing images for {llm_parsed_card_info.card_number}: {e}")
            return 0.0
    
    def _calculate_combined_similarity_score(
        self, llm_parsed_card_info: CardInfo, card_data: CardData
    ) -> float:
        """
        Calculate combined similarity score including both metadata and image comparison.
        
        Args:
            llm_parsed_card_info: CardInfo object from the image analysis
            card_data: CardData object from JSON
            
        Returns:
            float: Combined similarity score (0-1 range)
        """
        # Get metadata score
        metadata_score = self._calculate_metadata_similarity_score(llm_parsed_card_info, card_data)
        
        # Get image score
        image_score = self._calculate_image_similarity_score(llm_parsed_card_info, card_data)
        print(f"Comparing against image for {card_data.img_full_url}")
        print(f"Image score for {llm_parsed_card_info.card_number}: {image_score:.4f}")
        
        # Calculate combined score
        metadata_weight = sum(self.weights.values())
        total_weight = metadata_weight + (self.image_weight if image_score > 0 else 0)
        
        combined_score = (
            (metadata_score * metadata_weight + image_score * self.image_weight) 
            / total_weight
        )
        
        return combined_score
    
    def find_best_matches(
        self, 
        llm_parsed_card_info: CardInfo, 
        num_results: int = 5,
        min_score: float = 0.3,
        image_comparison_count: int = 3  # Number of top matches to apply image comparison to
    ) -> List[MatchResult]:
        """
        Find the best matching cards for a given CardInfo.
        
        Args:
            card_info: CardInfo object from the image analysis
            num_results: Maximum number of results to return
            min_score: Minimum similarity score to include in results
            image_comparison_count: Number of top matches to apply image comparison to
            
        Returns:
            List of MatchResult objects containing matched card data and score
        """
        # First phase: get preliminary matches based on metadata only
        preliminary_matches = []
        
        for card_data in self.all_cards:
            # Initial scoring without image comparison
            score = self._calculate_metadata_similarity_score(llm_parsed_card_info, card_data)
            if score >= min_score:
                # Create a copy of the card data with the score
                card_with_score = card_data.model_copy(update={"score": score})
                preliminary_matches.append(MatchResult(card=card_with_score, score=score))
        
        # Sort by initial score in descending order
        preliminary_matches.sort(key=lambda x: x.score, reverse=True)
        
        # Take top N preliminary matches for image comparison
        top_candidates = preliminary_matches[:image_comparison_count]
        final_matches = []
        
        # Second phase: Apply image comparison only to the top candidates if we have an image
        if llm_parsed_card_info.image_path:
            for match in top_candidates:
                # Recalculate score with image comparison
                new_score = self._calculate_combined_similarity_score(
                    llm_parsed_card_info, 
                    match.card
                )
                # Update the match with the new score that includes image comparison
                updated_card = match.card.model_copy(update={"score": new_score})
                final_matches.append(MatchResult(card=updated_card, score=new_score))
            
            # Add remaining preliminary matches without image comparison
            final_matches.extend(preliminary_matches[image_comparison_count:])
            
            # Re-sort all matches by the final score
            final_matches.sort(key=lambda x: x.score, reverse=True)
        else:
            # If no image path available, use the preliminary matches
            final_matches = preliminary_matches
        
        return final_matches[:num_results]
    
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
    
    def find_cards_by_base_id(self, base_id: str) -> List[CardData]:
        """
        Find all cards with the same base ID across all packs.
        
        Args:
            base_id: The base card ID (e.g., "OP01-001" or "001")
            
        Returns:
            List of CardData objects with matching base IDs
        """
        def extract_base_id(card_id: str) -> str:
            """Extract base card ID by removing parallel suffixes"""
            return card_id.split('_p')[0] if '_p' in card_id else card_id
        
        matching_cards = []
        target_base_id = extract_base_id(base_id)
        
        for card_data in self.all_cards:
            card_base_id = extract_base_id(card_data.id)
            
            # Normalize IDs for comparison
            normalized_target = target_base_id.upper().replace('-', '').replace('_', '')
            normalized_card = card_base_id.upper().replace('-', '').replace('_', '')
            
            if normalized_target == normalized_card:
                matching_cards.append(card_data)
        
        return matching_cards
    
    def find_pack_ids_by_base_id(self, base_id: str) -> List[str]:
        """
        Find all unique pack_ids for cards with the same base ID across all packs.

        Args:
            base_id: The base card ID (e.g., "OP01-001" or "001")
        Returns:
            List of unique pack_id strings
        """
        matching_cards = self.find_cards_by_base_id(base_id)
        pack_ids = set()
        for card in matching_cards:
            if hasattr(card, 'pack_id') and card.pack_id:
                pack_ids.add(card.pack_id)
        return list(pack_ids)
