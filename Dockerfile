# Simple Dockerfile for Railway deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright for graphics (optional)
RUN pip install playwright && playwright install chromium --with-deps || true

# Copy application code
COPY . .

# Expose port (Railway sets PORT env var, defaults to 3000)
EXPOSE 3000

# Use shell form CMD - this properly expands $PORT
# Railway sets PORT automatically, default to 3000 if not set
CMD uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-3000}
