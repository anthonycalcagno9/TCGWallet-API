"""
Tests for the card matcher service.
"""
import argparse
import json
from typing import Any, Dict

from app.models.card import CardInfo
from app.services.card_matcher import CardMatcher


def test_with_mock_card(mock_card: CardInfo):
    """
    Test with a mock card
    
    Args:
        mock_card: Mock card info for testing
    """
    print(f"Testing with mock card: {mock_card}")
    matcher = CardMatcher()
    matches = matcher.find_best_matches(mock_card, num_results=3)
    
    print(f"\nFound {len(matches)} matches:")
    for i, match_result in enumerate(matches, 1):
        card_data = match_result.card
        score = match_result.score
        print(f"\n--- Match #{i} (Score: {score:.2f}) ---")
        print(f"ID: {card_data.id}")
        print(f"Name: {card_data.name}")
        print(f"Category: {card_data.category}")
        print(f"Rarity: {card_data.rarity}")
        print(f"Colors: {card_data.colors}")
        print(f"Cost: {card_data.cost}")
        print(f"Counter: {card_data.counter}")


def test_with_custom_card(card_info: Dict[str, Any], weights: Dict[str, float]):
    """
    Test with a custom card and weights
    
    Args:
        card_info: Dict with card info to test
        weights: Dict with custom weights for matching
    """
    # Convert dict to CardInfo
    info = CardInfo(**card_info)
    
    print(f"Testing with custom card: {info}")
    print(f"Using weights: {weights}")
    
    matcher = CardMatcher(weights=weights)
    matches = matcher.find_best_matches(info, num_results=3)
    
    print(f"\nFound {len(matches)} matches:")
    for i, match_result in enumerate(matches, 1):
        card_data = match_result.card
        score = match_result.score
        print(f"\n--- Match #{i} (Score: {score:.2f}) ---")
        print(f"ID: {card_data.id}")
        print(f"Name: {card_data.name}")
        print(f"Category: {card_data.category}")
        print(f"Rarity: {card_data.rarity}")
        print(f"Colors: {card_data.colors}")
        print(f"Cost: {card_data.cost}")
        print(f"Counter: {card_data.counter}")
        print(f"Types: {card_data.types}")


def main():
    """Run the card matcher tests."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Test the CardMatcher class')
    parser.add_argument('--mock', action='store_true', 
                        help='Test with mock card from models')
    parser.add_argument('--card-json', type=str,
                        help='JSON string with card info to test')
    parser.add_argument('--card-file', type=str, 
                        help='JSON file with card info to test')
    parser.add_argument('--weights-json', type=str,
                        help='JSON string with custom weights')
    parser.add_argument('--weights-file', type=str,
                        help='JSON file with custom weights')
    args = parser.parse_args()
    
    # Default weights
    weights = {
        "id": 7.0,
        "cost": 5.0,
        "name": 3.0,
        "color": 3.0,
        "counter": 3.0,
        "category": 2.0,
        "rarity": 2.0
    }
    
    # Load custom weights if provided
    if args.weights_json:
        weights.update(json.loads(args.weights_json))
    elif args.weights_file:
        with open(args.weights_file, 'r') as f:
            weights.update(json.load(f))
    
    if args.mock:
        # Import mock card from models
        from app.models import mock_card
        # Test with mock card
        test_with_mock_card(mock_card)
    elif args.card_json or args.card_file:
        # Load card info
        if args.card_json:
            card_info = json.loads(args.card_json)
        else:
            with open(args.card_file, 'r') as f:
                card_info = json.load(f)
        
        # Test with custom card
        test_with_custom_card(card_info, weights)
    else:
        # No card specified, use a default test case
        card_info = {
            "name": "Monkey D. Luffy",
            "card_number": "ST14-001",
            "type": "Leader",
            "cost": 5,
            "color": "Black"
        }
        test_with_custom_card(card_info, weights)


if __name__ == "__main__":
    main()
