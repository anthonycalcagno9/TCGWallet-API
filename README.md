# TCGWallet-API

TCGWallet API is a service for identifying and pricing trading card game (TCG) cards using image recognition and AI. The service can analyze card images, extract information, and match them against a database of cards.

## Project Structure

```
TCGWallet-API/
├── app/                  # Application package
│   ├── api/              # API endpoints
│   │   ├── card.py       # Card matching endpoints
│   │   ├── image.py      # Image analysis endpoints
│   │   └── tcgplayer.py  # TCGPlayer data endpoints
│   ├── core/             # Core functionality and configuration
│   │   └── config.py     # App settings and configuration
│   ├── db/               # Database models and connections
│   ├── models/           # Pydantic models
│   │   ├── card.py       # Card data models
│   │   └── tcgplayer.py  # TCGPlayer API models
│   ├── services/         # Business logic services
│   │   ├── card_matcher.py  # Card matching service
│   │   └── tcgplayer_api.py # TCGPlayer API client
│   ├── tests/            # Test modules
│   │   ├── test_api.py      # TCGPlayer API tests
│   │   └── test_card_matcher.py  # Card matcher tests
│   └── utils/            # Utility functions and helpers
│       ├── errors.py     # Error handling utilities
│       └── image.py      # Image processing utilities
├── data/                 # Data files
│   └── cards_by_pack/    # Card data organized by pack
├── docs/                 # Documentation
│   └── api.md            # API documentation
├── mocks/                # Mock data and test images
└── main.py               # Application entry point
```

## How to Run Locally

### Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) - The Python package installer

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/TCGWallet-API.git
cd TCGWallet-API
```

2. Run the setup script (installs dependencies using uv):

```bash
./setup.sh
```

Or manually install dependencies:

```bash
uv pip install -e ".[dev]"
```

3. Run the service:

```bash
# Make sure to activate the virtual environment first
source .venv/bin/activate
python run.py
```

The API will be available at http://localhost:8000

## API Endpoints

- `/api/image/analyze-image` - Upload and analyze card images
- `/api/card/match-card` - Match card info against the database  
- `/api/tcgplayer/groups` - Get TCGPlayer card groups/sets
- `/api/tcgplayer/products/{group_id}` - Get products for a set
- `/api/tcgplayer/prices/{group_id}` - Get prices for a set

## Linting

```bash
uv run ruff check
```

## Testing

Run the card matcher test tool:

```bash
python -m app.tests.test_card_matcher --mock
```

Test the TCGPlayer API client:

```bash
python -m app.tests.test_api
```

## Example API Call

```bash
curl -X POST "http://localhost:8000/api/image/analyze-image" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/card.png;type=image/png"
```
