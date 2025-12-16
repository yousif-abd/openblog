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

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port (Railway sets PORT env var)
EXPOSE 3000

# Use entrypoint script - Railway may override with this, so ensure it exists
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
