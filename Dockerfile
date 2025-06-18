# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies and libraries required for OpenCV and other common Python packages
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install uv (Rust-based Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && export PATH="/root/.local/bin:$PATH" \
    && /root/.local/bin/uv venv \
    && /root/.local/bin/uv pip install -e ".[dev]"

# Expose port 8000 for the application
EXPOSE 8000

# Activate virtualenv and run the app
CMD ["/app/.venv/bin/python", "run.py"]
