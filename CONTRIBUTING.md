# Contributing to TCGWallet API

Thank you for considering contributing to TCGWallet API! Here are some guidelines to help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TCGWallet-API.git
cd TCGWallet-API
```

2. Install dependencies:
```bash
pip install -e .
# OR
uv install -e .
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key"
export CARDS_DATA_DIR="data/cards_by_pack"
```

4. Run the development server:
```bash
python run.py
# OR
uvicorn main:app --reload
```

## Project Structure

Please follow the established project structure:

- Put API endpoints in `app/api/`
- Put models in `app/models/`
- Put business logic in `app/services/`
- Put utilities in `app/utils/`
- Put tests in `app/tests/`

## Code Style

We use Ruff for linting:

```bash
uv run ruff check
```

## Testing

Run tests for the card matcher:

```bash
python -m app.tests.test_card_matcher --mock
```

Test the TCGPlayer API:

```bash
python -m app.tests.test_api
```

## Pull Requests

1. Create a branch for your feature or bugfix
2. Write tests for your changes if applicable
3. Run the linter and tests
4. Submit a pull request with a clear description of the changes

Thank you for your contribution!
