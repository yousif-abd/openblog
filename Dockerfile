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

# Expose port (Railway sets PORT env var)
EXPOSE 3000

# Use uvicorn directly (installed via uvicorn[standard] in requirements.txt)
# Railway auto-detection expects 'uvicorn' command in PATH
CMD ["uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "3000"]
