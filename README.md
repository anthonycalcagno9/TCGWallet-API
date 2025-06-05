# TCGWallet-API

## How to run locally
`brew install uv`
`uv run fastapi dev main.py`

## Linting 
`uv run ruff check`

## Test local
```bash
curl -X POST "http://localhost:8000/analyze-image" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/OP10-009.png;type=image/png"
```
