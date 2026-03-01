"""
Integration Guide for Refactored Macro Engine API

This guide explains the new three-stage pipeline architecture.
"""

# ============================================================================
# Quick Start
# ============================================================================

"""
1. Run the API:
   python api_server_refactored.py
   
   Server runs on http://localhost:10000
   API docs at http://localhost:10000/docs
   
2. Test the pipeline (example dates, adjust to your data):

   Stage 1 - Regime Mapping:
   POST http://localhost:10000/recommend/start
   {
     "target_date": "01-04-2009"
   }
   
   Stage 2 - Investor Allocation:
   POST http://localhost:10000/recommend/investor
   {
     "target_date": "01-04-2009",
     "investor_type": "Balanced"
   }
   
   Stage 3 - Portfolio Construction:
   POST http://localhost:10000/recommend/final
   {
     "target_date": "01-04-2009",
     "investor_type": "Balanced"
   }
"""

# ============================================================================
# Architecture Overview
# ============================================================================

"""
PROJECT STRUCTURE:
├── api_server_refactored.py      ← Main application (FastAPI setup)
├── services/
│   ├── __init__.py
│   ├── pipeline.py               ← Subprocess execution for Passes 4-6
│   └── validation.py             ← Input validation
├── routers/
│   ├── __init__.py
│   └── recommendations.py        ← API endpoints
└── Pass 4-6/                     ← Existing pass scripts

KEY FEATURES:
✅ Clean separation of concerns (services, routers, main app)
✅ Multi-stage pipeline with proper dependencies
✅ Subprocess isolation - each pass runs independently
✅ Comprehensive error handling and logging
✅ Async endpoints for better performance
✅ Validation at request boundaries
✅ Production-quality error messages
"""

# ============================================================================
# Three-Stage Pipeline
# ============================================================================

"""
STAGE 1: PASS 4 - REGIME MAPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Endpoint:     POST /recommend/start
Input:        { "target_date": "DD-MM-YYYY" }
Output:       Regime detection + factor tilts
Depends On:   None
Execution:    Runs Pass 4 - Regime Mapping script
Purpose:      Detect active market regimes and generate factor weights

Example:
  POST /recommend/start
  { "target_date": "01-04-2009" }
  
  Response:
  {
    "status": "success",
    "stage": "pass4",
    "target_date": "01-04-2009",
    "message": "Pass 4 completed...",
    "data": {
      "date": "01-04-2009",
      "active_regimes": ["High_Inflation", "Weak_Growth"],
      "factor_weights": {...}
    }
  }


STAGE 2: PASS 5 - INVESTOR ALLOCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Endpoint:     POST /recommend/investor
Input:        { "target_date": "DD-MM-YYYY", "investor_type": "..." }
Output:       Investor-specific portfolio allocation
Depends On:   Pass 4 (uses factor_tilt_latest.json)
Execution:    Runs Pass 5 - Investor Allocator script
Purpose:      Customize portfolio allocation for investor profile

Investor Types:
  - "Conservative": Low risk, stable returns
  - "Balanced": Moderate risk-return tradeoff
  - "Aggressive": High risk, growth-focused

Example:
  POST /recommend/investor
  {
    "target_date": "01-04-2009",
    "investor_type": "Balanced"
  }
  
  Response:
  {
    "status": "success",
    "stage": "pass5",
    "target_date": "01-04-2009",
    "investor_type": "Balanced",
    "message": "Pass 5 completed...",
    "data": {
      "investor_type": "Balanced",
      "portfolio_allocation": {...}
    }
  }


STAGE 3: PASS 6 - PORTFOLIO CONSTRUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Endpoint:     POST /recommend/final
Input:        { "target_date": "DD-MM-YYYY", "investor_type": "..." }
Output:       Final portfolio with asset-level allocations
Depends On:   Pass 5 (uses portfolio_recommendation_latest.json)
Execution:    Runs Pass 6 - Portfolio Constructor script
Purpose:      Construct final execution-ready portfolio

Example:
  POST /recommend/final
  {
    "target_date": "01-04-2009",
    "investor_type": "Balanced"
  }
  
  Response:
  {
    "status": "success",
    "stage": "pass6",
    "target_date": "01-04-2009",
    "investor_type": "Balanced",
    "message": "Pass 6 completed...",
    "data": {
      "portfolio": {
        "VTV": 0.25,
        "QUAL": 0.25,
        "MTUM": 0.25,
        "CASH": 0.25
      }
    }
  }
"""

# ============================================================================
# Service Layer Architecture
# ============================================================================

"""
SERVICES/PIPELINE.PY
═══════════════════════════════════════════════════════════════════════════

Functions:
  run_pass4(target_date: str) → Dict[str, Any]
    - Executes Pass 4 script via subprocess
    - Validates target_date format
    - Loads and returns factor_tilt_latest.json
    - Raises Pass4ExecutionError on failure
    
  run_pass5(target_date: str, investor_type: str) → Dict[str, Any]
    - Executes Pass 5 script via subprocess
    - Depends on Pass 4 output being present
    - Loads and returns portfolio_recommendation_latest.json
    - Raises Pass5ExecutionError on failure
    
  run_pass6(target_date: str, investor_type: str) → Dict[str, Any]
    - Executes Pass 6 script via subprocess
    - Depends on Pass 5 output being present
    - Loads and returns portfolio_execution_latest.json
    - Raises Pass6ExecutionError on failure

Key Features:
  ✓ Subprocess isolation - each pass runs independently
  ✓ Captured stdout/stderr for debugging
  ✓ Timeout protection (300s default)
  ✓ Logging at each stage
  ✓ Error propagation with context
"""

# ============================================================================
# Error Handling
# ============================================================================

"""
HTTP Status Codes & Responses:

400 Bad Request
  - Invalid date format
  - Invalid investor type
  - Missing required fields
  
  Example:
  {
    "detail": "Invalid date format: 01/04/2009. Expected DD-MM-YYYY"
  }

500 Internal Server Error
  - Pass 4/5/6 execution failed
  - Script output file not found
  - Unexpected error
  
  Example:
  {
    "detail": "Pass 4 failed: ModuleNotFoundError: No module named 'pandas'"
  }

LOGGING:
  All stages are logged to stdout and optionally to logs/api.log
  Debug level captures subprocess output for troubleshooting
"""

# ============================================================================
# Testing the Pipeline
# ============================================================================

"""
USING CURL:

1. Start regime mapping:
   curl -X POST http://localhost:10000/recommend/start \
     -H "Content-Type: application/json" \
     -d '{"target_date": "01-04-2009"}'

2. Allocate investor portfolio:
   curl -X POST http://localhost:10000/recommend/investor \
     -H "Content-Type: application/json" \
     -d '{"target_date": "01-04-2009", "investor_type": "Balanced"}'

3. Get final portfolio:
   curl -X POST http://localhost:10000/recommend/final \
     -H "Content-Type: application/json" \
     -d '{"target_date": "01-04-2009", "investor_type": "Balanced"}'

USING PYTHON:
   See test_api.py for complete integration tests
"""

# ============================================================================
# Configuration & Customization
# ============================================================================

"""
ALLOWED INVESTOR TYPES:
Edit services/validation.py, validate_investor_type() to add more types:

    valid_types = [
        "Conservative",
        "Balanced", 
        "Aggressive",
        "Growth",      ← Add custom types here
        "Income"       ← And here
    ]

TIMEOUT:
Default timeout for each pass is 300 seconds.
Adjust in services/pipeline.py, run_subprocess():

    result = subprocess.run(..., timeout=600)  ← Change to 600s

CORS:
Allow specific origins in api_server_refactored.py:

    allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"]

LOGGING:
Enable debug logging in api_server_refactored.py:

    logging.basicConfig(level=logging.DEBUG)
"""

# ============================================================================
# Deployment
# ============================================================================

"""
LOCAL DEVELOPMENT:
  python api_server_refactored.py

PRODUCTION (Gunicorn + Uvicorn):
  gunicorn api_server_refactored:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:10000 \
    --access-logfile - \
    --error-logfile -

DOCKER:
  # Use existing Dockerfile, it will work with the refactored code
  docker build -t macro-engine .
  docker run -p 10000:10000 macro-engine

RENDER / RAILWAY:
  The refactored code requires the same dependencies as before.
  Ensure requirements.txt includes all packages (should be fixed by now).
"""

# ============================================================================
# Common Issues & Debugging
# ============================================================================

"""
ISSUE: "No module named 'pandas'"
SOLUTION: Run pip install -r requirements.txt

ISSUE: "Pass 4 did not generate factor_tilt_latest.json"
SOLUTION: Check if the Pass 4 script expects arguments or environment variables
          Inspect logs for Pass 4 subprocess errors

ISSUE: "Invalid date format"
SOLUTION: Ensure date is in DD-MM-YYYY format, e.g., "01-04-2009"
          Check that the date exists in your data

ISSUE: "Pass 5/6 fails after Pass 4 succeeds"
SOLUTION: Pass 5 depends on Pass 4 output file being present.
          Check that factor_tilt_latest.json was generated by Pass 4.
          Similarly, Pass 6 depends on Pass 5 output.

DEBUGGING:
  1. Enable debug logging (set level=logging.DEBUG)
  2. Check logs/api.log for detailed subprocess output
  3. Run Pass scripts manually to test:
     python Pass\ 4\ -\ Regime\ Mapping/outputs/pass4_regime_mapper.py \
       --target-date 01-04-2009
"""

print(__doc__)
