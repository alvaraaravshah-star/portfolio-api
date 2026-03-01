"""
Refactored FastAPI Server - Macro Engine Interactive Application

Architecture:
- services/pipeline.py: Subprocess execution for Pass 4, 5, 6
- services/validation.py: Input validation
- routers/recommendations.py: API endpoints for the pipeline
- This main file: App setup, middleware, static files, root endpoints

Multi-Stage Pipeline:
1. POST /recommend/start → Pass 4 (Regime Mapping)
2. POST /recommend/investor → Pass 5 (Investor Allocation)
3. POST /recommend/final → Pass 6 (Portfolio Construction)
"""

import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from routers.recommendations import router as recommendations_router

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "api.log") if (PROJECT_ROOT / "logs").exists() else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="Macro Engine API",
    description="Multi-stage pipeline API for regime-based portfolio construction",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# Middleware
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Static Files
# ============================================================================

# Mount web UI
WEB_DIR = PROJECT_ROOT / "web"
if WEB_DIR.exists():
    try:
        app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
        logger.info(f"Mounted web UI at /web from {WEB_DIR}")
    except Exception as e:
        logger.warning(f"Could not mount web UI: {e}")

# Mount static assets
STATIC_DIR = WEB_DIR / "static"
if STATIC_DIR.exists():
    try:
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
        logger.info(f"Mounted static assets at /static from {STATIC_DIR}")
    except Exception as e:
        logger.warning(f"Could not mount static assets: {e}")


# ============================================================================
# Response Models
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str


class InfoResponse(BaseModel):
    """API information response."""
    service: str
    version: str
    description: str
    stages: list[str]


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get(
    "/",
    response_model=InfoResponse,
    summary="API Information",
    tags=["health"]
)
async def root() -> InfoResponse:
    """
    GET /
    
    Returns information about the Macro Engine API.
    """
    return InfoResponse(
        service="Macro Engine API",
        version="2.0.0",
        description="Multi-stage pipeline for regime-based portfolio construction",
        stages=[
            "Pass 4: Regime Mapping (/recommend/start)",
            "Pass 5: Investor Allocation (/recommend/investor)",
            "Pass 6: Portfolio Construction (/recommend/final)"
        ]
    )


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    tags=["health"]
)
async def health_check() -> HealthCheckResponse:
    """
    GET /health
    
    Health check endpoint. Returns 200 OK if the service is running.
    """
    logger.info("Health check performed")
    return HealthCheckResponse(
        status="healthy",
        service="Macro Engine API",
        version="2.0.0"
    )


@app.get(
    "/api/pipeline",
    summary="Pipeline Documentation",
    tags=["documentation"]
)
async def pipeline_docs():
    """
    GET /api/pipeline
    
    Returns documentation about the three-stage pipeline.
    """
    return JSONResponse(
        content={
            "pipeline": "Three-stage multi-process recommendation pipeline",
            "stages": [
                {
                    "stage": "Pass 4",
                    "name": "Regime Mapping",
                    "endpoint": "POST /recommend/start",
                    "input": {"target_date": "YYYY-DD-MM"},
                    "output": "Regime detection and factor tilts",
                    "description": "Analyzes market conditions and detects active regimes"
                },
                {
                    "stage": "Pass 5",
                    "name": "Investor Allocation",
                    "endpoint": "POST /recommend/investor",
                    "input": {"target_date": "YYYY-DD-MM", "investor_type": "Conservative|Balanced|Aggressive"},
                    "output": "Investor-specific portfolio allocation",
                    "description": "Allocates portfolio based on regime and investor profile",
                    "requires": "Pass 4 output"
                },
                {
                    "stage": "Pass 6",
                    "name": "Portfolio Construction",
                    "endpoint": "POST /recommend/final",
                    "input": {"target_date": "YYYY-DD-MM", "investor_type": "Conservative|Balanced|Aggressive"},
                    "output": "Final portfolio execution plan",
                    "description": "Constructs final portfolio with asset-level allocations",
                    "requires": "Pass 5 output"
                }
            ],
            "example_flow": [
                "POST /recommend/start with target_date='2009-01-04'",
                "POST /recommend/investor with target_date='2009-01-04' and investor_type='Balanced'",
                "POST /recommend/final with target_date='2009-01-04' and investor_type='Balanced'"
            ]
        }
    )


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(recommendations_router)

logger.info("Macro Engine API v2.0.0 initialized with multi-stage pipeline")
logger.info("Available endpoints: /recommend/start, /recommend/investor, /recommend/final")


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": str(exc.detail)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"Unexpected exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": "Internal server error"
        }
    )


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting Macro Engine API server...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info("Pipeline stages ready:")
    logger.info("  - Pass 4: Regime Mapping")
    logger.info("  - Pass 5: Investor Allocation")
    logger.info("  - Pass 6: Portfolio Construction")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Macro Engine API server...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=10000,
        log_level="info"
    )
