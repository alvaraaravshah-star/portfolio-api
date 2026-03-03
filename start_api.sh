#!/bin/bash

#!/bin/bash

# FastAPI Server Startup Script
#
# This helper launches the single, canonical ASGI application defined in
# ``main.py``.  For development you can directly call uvicorn as shown below.

echo "Installing dependencies..."
pip install -r requirements.txt

PORT=${PORT:-10000}
echo "Starting FastAPI server on port $PORT..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload

echo "API server running at http://localhost:$PORT"
echo "API documentation available at http://localhost:$PORT/docs"
