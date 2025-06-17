# TCGWallet API Documentation

This document provides details about the TCGWallet API endpoints and usage examples.

## Base URL

All API endpoints are accessible under the `/api` prefix:

```
http://localhost:8000/api
```

## Authentication

Currently, the API does not require authentication.

## Endpoints

### Image Analysis

#### Analyze Card Image

```
POST /api/image/analyze-image
```

Upload a card image for analysis and recognition.

**Request**:
- Content-Type: `multipart/form-data`
- Body: 
  - `file`: Image file (JPEG or PNG)

**Response**:
```json
{
  "description": {
    "name": "Monkey D. Luffy",
    "type": "Leader",
    "cost": 5,
    "rarity": "Secret Rare",
    "color": "Red",
    "counter": 2000,
    "trait": "Straw Hat Crew",
    "card_number": "OP01-001"
  },
  "filename": "luffy.jpg",
  "size": 123456,
  "best_match": {
    "card": {
      "id": "OP01-001",
      "pack_id": "OP01",
      "name": "Monkey D. Luffy",
      "rarity": "Secret Rare",
      "category": "Leader",
      "colors": ["Red"],
      "cost": 5,
      "counter": 2000,
      "types": ["Straw Hat Crew"],
      "effect": "Once per turn, when you activate the Main ability...",
      "score": 0.95
    },
    "score": 0.95,
    "tcgplayer_product_id": 12345,
    "tcgplayer_price": 25.99
  },
  "matches": [
    {
      "card": {
        "id": "OP01-001",
        "pack_id": "OP01",
        "name": "Monkey D. Luffy",
        "rarity": "Secret Rare",
        "category": "Leader",
        "colors": ["Red"],
        "cost": 5,
        "counter": 2000,
        "types": ["Straw Hat Crew"],
        "effect": "Once per turn, when you activate the Main ability...",
        "score": 0.95
      },
      "score": 0.95,
      "tcgplayer_product_id": 12345,
      "tcgplayer_price": 25.99
    }
  ]
}
```

### Card Matching

#### Match Card

```
POST /api/card/match-card
```

Match card information against the database.

**Request**:
- Content-Type: `application/json`
- Body:
```json
{
  "name": "Monkey D. Luffy",
  "type": "Leader",
  "card_number": "OP01-001",
  "color": "Red"
}
```

**Response**:
```json
{
  "matches": [
    {
      "card": {
        "id": "OP01-001",
        "name": "Monkey D. Luffy",
        "rarity": "Secret Rare",
        "category": "Leader",
        "colors": ["Red"],
        "score": 0.95
      },
      "score": 0.95
    }
  ]
}
```

### TCGPlayer Data

#### Get Card Groups/Sets

```
GET /api/tcgplayer/groups
```

**Response**:
```json
{
  "groups": [
    {
      "groupId": 23766,
      "name": "Royal Blood",
      "abbreviation": "OP10",
      "isSupplemental": false,
      "publishedOn": "2023-06-02",
      "categoryId": 68
    }
  ]
}
```

#### Get Products for a Group

```
GET /api/tcgplayer/products/{group_id}
```

**Response**:
```json
{
  "products": [
    {
      "productId": 456789,
      "name": "Monkey D. Luffy",
      "cleanName": "Monkey D Luffy",
      "imageUrl": "https://example.com/card.jpg",
      "url": "https://tcgplayer.com/card/456789"
    }
  ]
}
```

#### Get Prices for a Group

```
GET /api/tcgplayer/prices/{group_id}
```

**Response**:
```json
{
  "prices": [
    {
      "productId": 456789,
      "lowPrice": 10.99,
      "midPrice": 15.50,
      "highPrice": 25.00,
      "marketPrice": 18.75
    }
  ]
}
```

## Error Responses

The API returns standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `500`: Server Error

Error responses include a detail message:

```json
{
  "detail": "Only JPEG and PNG images are supported"
}
```
