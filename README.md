# TCGWallet-API
api for tcgwallet

curl -X POST "http://localhost:8000/analyze-image" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/Users/anthonycalcagno/Desktop/OP10-009.png;type=image/png"
