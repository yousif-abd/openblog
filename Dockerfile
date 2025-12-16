FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip
RUN curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py --break-system-packages && \
    python -m pip install --upgrade pip setuptools wheel --break-system-packages

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m pip install -r requirements.txt --break-system-packages

# Install Playwright Chromium
RUN python -m playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command - use shell form to expand $PORT
CMD python3 -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-8000}

