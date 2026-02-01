#!/bin/bash

# FastAPI Server Startup Script
# Starts the Macro Engine API on port 8000

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting FastAPI server..."
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

echo "API server running at http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
