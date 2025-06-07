#!/bin/bash
# Setup script for TCGWallet API development environment

# Check if Python is installed
if ! command -v python >/dev/null 2>&1; then
  echo "Python is required but not installed. Please install Python and try again."
  exit 1
fi

# Check if uv is installed, install if not
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv package manager..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Make sure uv is in path
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file to add your API keys"
  else
    echo "Creating empty .env file..."
    touch .env
    echo "# Add your environment variables here" > .env
    echo "OPENAI_API_KEY=" >> .env
  fi
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating a virtual environment..."
  uv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies using uv
echo "Installing project dependencies..."
uv pip install -e ".[dev]"

echo "Setup complete! You can now run the project with:"
echo "python run.py"
echo ""
echo "Make sure to update your .env file with your API keys"
