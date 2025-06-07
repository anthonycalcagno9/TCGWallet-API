# Card Matching Functionality

This module provides functionality to match card information from image recognition with the card database.

## How it Works

The `CardMatcher` class implements a weighted scoring system to compare a `CardInfo` object with card data from the JSON files and find the closest match. The comparison uses the following fields:

- Card ID/Number: Highest weight (default: 7.0)
- Cost: Second highest weight (default: 5.0)
- Name: Medium weight (default: 3.0)
- Color: Medium weight (default: 3.0)
- Counter: Medium weight (default: 3.0)
- Type/Category: Lower weight (default: 2.0)
- Rarity: Lower weight (default: 2.0)

## Usage

### Through the API

The card matching functionality is integrated into the API:

1. `/analyze-image` - Upload an image of a card to get its info and potential matches
2. `/match-card` - Match a card against the database using custom weights for testing

### Through the Test Script

The `test_card_matcher.py` script allows you to test the card matching functionality directly:

```bash
# Test with the default mock card
python test_card_matcher.py --mock

# Test with a custom card provided as JSON
python test_card_matcher.py --card-json '{"name": "Monkey D. Luffy", "card_number": "ST14-001", "type": "Leader", "cost": 5, "color": "Black"}'

# Test with custom weights
python test_card_matcher.py --card-json '{"name": "Monkey D. Luffy"}' --weights-json '{"id": 10.0, "name": 5.0}'

# Test with a card from a file
python test_card_matcher.py --card-file my_card.json --weights-file my_weights.json
```

### Through Direct Import

```python
from main import CardInfo
from card_matcher import CardMatcher

# Create a card info object
card_info = CardInfo(
    name="Monkey D. Luffy",
    card_number="ST14-001",
    type="Leader",
    cost=5,
    color="Black"
)

# Create a matcher with custom weights
weights = {
    "id": 10.0,  # Increase weight for ID matching
    "cost": 5.0,
    "name": 3.0,
    "color": 3.0,
    "counter": 3.0,
    "category": 2.0,
    "rarity": 2.0
}
matcher = CardMatcher(weights=weights)

# Find the best matches
matches = matcher.find_best_matches(card_info, num_results=3)

# Print the matches
for card_data, score in matches:
    print(f"Match: {card_data['name']} (ID: {card_data['id']}) - Score: {score:.2f}")
```

## Customizing Weights

To adjust how the matching works, you can modify the weights:

- Increase the weight for fields that are more reliable in your data
- Decrease the weight for fields that are less reliable

For example, if your image recognition is very good at identifying card numbers but often gets the cost wrong, you could increase the weight for "id" and decrease it for "cost".

## Example Weights Configuration

```json
{
  "id": 7.0,
  "cost": 5.0,
  "name": 3.0,
  "color": 3.0,
  "counter": 3.0,
  "category": 2.0,
  "rarity": 2.0
}
```
