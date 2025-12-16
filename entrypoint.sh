#!/bin/bash
set -e

# Railway provides PORT env var - use it directly with fallback
if [ -z "$PORT" ]; then
    export PORT=3000
fi

echo "Starting uvicorn on port $PORT"

# Start uvicorn directly with Railway's PORT
exec python3 -c "import uvicorn; import os; uvicorn.run('service.api:app', host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))"

