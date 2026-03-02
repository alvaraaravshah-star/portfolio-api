#!/bin/bash

# FastAPI Server Startup Script
# Historically this script launched the legacy `api_server.py` implementation
# which exposed a single POST /recommend endpoint.  The refactored version with
# the multi‑stage pipeline (including POST /recommend/start, /investor, /final)
# lives in `api_server_refactored.py` and is what the tests and documentation
# expect today.  If you run the old server you will see 404s for
# `/recommend/start` as you reported in your error message.

echo "Installing dependencies..."
pip install -r requirements.txt

# Launch the refactored API by default.  If you really want to run the old
# single‑endpoint server you can still call `python -m uvicorn api_server:app`
# manually, but be aware tests/clients expect the newer routes.
PORT=${PORT:-10000}
echo "Starting FastAPI server (refactored) on port $PORT..."
python -m uvicorn api_server_refactored:app --host 0.0.0.0 --port $PORT --reload

echo "API server running at http://localhost:$PORT"
echo "API documentation available at http://localhost:$PORT/docs"
