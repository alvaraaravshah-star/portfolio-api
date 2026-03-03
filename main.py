"""ASGI entry point for deployment.

This module defines the single FastAPI application instance that
Render, Docker, and other deployment platforms should import.  The
start command is typically:

    uvicorn main:app --host 0.0.0.0 --port 10000

Only one :class:`FastAPI` instance should exist in the project; any
legacy files such as ``api_server.py`` have been removed.
"""

import logging

from fastapi import FastAPI

from routers.recommendations import router as recommend_router

# Configure simple logging for request handling and pipeline stages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Macro Engine API",
    description="Three‑stage recommendation pipeline (Pass 4/5/6)",
    version="1.0.0",
)

# only one router with prefix "/recommend" is included
app.include_router(recommend_router)


@app.get("/", tags=["health"])
async def info():
    """Basic information about the service."""
    return {
        "service": "Macro Engine API",
        "stages": [
            "POST /recommend/start",
            "POST /recommend/investor",
            "POST /recommend/final",
        ],
    }


@app.get("/health", tags=["health"])
async def health():
    """Simple health check."""
    return {"status": "healthy"}
