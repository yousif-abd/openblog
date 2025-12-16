#!/bin/bash
set -e

# Get PORT from environment, default to 3000
PORT=${PORT:-3000}

# Use Python to start uvicorn - this ensures PORT is read from env
exec python3 -m uvicorn service.api:app --host 0.0.0.0 --port "$PORT"

