#!/usr/bin/env python
"""
Run the TCGWallet API server.

This script uses uvicorn to serve the FastAPI application.
The application is configured to run in development mode with auto-reload enabled.
In production, consider using a proper ASGI server deployment.

Make sure to run this script in the virtual environment:
    source .venv/bin/activate && python run.py
"""
import os
import sys

import uvicorn

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
