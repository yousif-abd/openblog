#!/bin/bash
set -e

# Get PORT from environment, default to 3000
PORT=${PORT:-3000}

# Execute uvicorn with the port
exec uvicorn service.api:app --host 0.0.0.0 --port "$PORT"

