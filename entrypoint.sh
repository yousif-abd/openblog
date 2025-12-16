#!/bin/sh
set -e

# Railway provides PORT env var - use it directly
# Use uvicorn executable directly (installed via uvicorn[standard])
exec uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-3000}

