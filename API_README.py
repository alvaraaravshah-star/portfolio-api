"""
Refactored Macro Engine API - README

A production-quality FastAPI backend implementing a three-stage pipeline
for regime-based portfolio construction.

✨ Key Improvements Over Original:
  - Clean separation of concerns (services, routers, main app)
  - Proper error handling and HTTP status codes
  - Comprehensive logging for debugging
  - Input validation at request boundaries
  - Async endpoints for better concurrency
  - Type hints throughout for IDE support
  - Pydantic models for request/response validation
  - Production-ready error messages
  - Easy to extend with new endpoints or stages
"""

# ============================================================================
# QUICK START
# ============================================================================

"""
1. Install dependencies (if not already done):
   pip install -r requirements.txt

2. Run the refactored API server:
   python api_server_refactored.py
   
   Output:
   INFO:     Uvicorn running on http://0.0.0.0:10000
   
3. Access the API:
   - Interactive docs: http://localhost:10000/docs
   - OpenAPI schema: http://localhost:10000/openapi.json
   - Health check: http://localhost:10000/health

4. Test the pipeline (see test_api.py for full tests):
   python test_api.py
"""

# ============================================================================
# ARCHITECTURE OVERVIEW
# ============================================================================

"""
PROJECT STRUCTURE:

├── api_server_refactored.py      ← Main FastAPI application
│                                   Sets up app, middleware, static files
│                                   Includes startup/shutdown hooks
│                                   Handles root endpoints and exception handlers
│
├── services/
│   ├── __init__.py
│   ├── pipeline.py               ← Subprocess execution
│   │                               - run_pass4(target_date)
│   │                               - run_pass5(target_date, investor_type)
│   │                               - run_pass6(target_date, investor_type)
│   │                               - Custom exception classes
│   │
│   └── validation.py             ← Input validation
│                                   - validate_date_format()
│                                   - validate_investor_type()
│                                   - validate_recommendation_request()
│
├── routers/
│   ├── __init__.py
│   └── recommendations.py        ← API endpoints
│                                   - POST /recommend/start (Pass 4)
│                                   - POST /recommend/investor (Pass 5)
│                                   - POST /recommend/final (Pass 6)
│
├── Pass 4 - Regime Mapping/      ← Existing pass scripts
├── Pass 5 - Portfolio Scoring/
├── Pass 6 - Portfolio Construction/
│
└── web/                          ← Static web UI (auto-mounted)


EXECUTION FLOW:

   Client Request
        ↓
   FastAPI Router (routers/recommendations.py)
        ↓
   Input Validation (services/validation.py)
        ↓
   Pipeline Service (services/pipeline.py)
        ↓
   Subprocess Execution (Pass 4, 5, or 6)
        ↓
   Output Loading & Response Formatting
        ↓
   HTTP Response (structured JSON)
"""

# ============================================================================
# API ENDPOINTS
# ============================================================================

"""
ENDPOINT 1: POST /recommend/start
═══════════════════════════════════════════════════════════════════════════
Executes Pass 4: Regime Mapping

Input:
  {
    "target_date": "DD-MM-YYYY"  (required)
  }

Output (200 OK):
  {
    "status": "success",
    "stage": "pass4",
    "target_date": "01-04-2009",
    "message": "Pass 4 (Regime Mapping) completed successfully...",
    "data": {
      "date": "01-04-2009",
      "active_regimes": ["High_Inflation", "Weak_Growth"],
      "regime_strength": {...},
      "factor_weights": {
        "Value": 0.4,
        "Quality": 0.3,
        "Momentum": 0.3
      }
    }
  }

Error (400 Bad Request):
  {
    "detail": "Invalid date format: 2009-04-01. Expected DD-MM-YYYY"
  }

Error (500 Internal Server Error):
  {
    "detail": "Pass 4 failed: ModuleNotFoundError: No module named 'pandas'"
  }


ENDPOINT 2: POST /recommend/investor
═══════════════════════════════════════════════════════════════════════════
Executes Pass 5: Investor Allocation (depends on Pass 4)

Input:
  {
    "target_date": "DD-MM-YYYY",           (required)
    "investor_type": "Conservative|Balanced|Aggressive"  (required)
  }

Output (200 OK):
  {
    "status": "success",
    "stage": "pass5",
    "target_date": "01-04-2009",
    "investor_type": "Balanced",
    "message": "Pass 5 (Investor Allocation) completed successfully...",
    "data": {
      "investor_type": "Balanced",
      "portfolio_allocation": {
        "Value": 0.35,
        "Quality": 0.35,
        "Momentum": 0.30
      }
    }
  }

Error Responses: Similar structure to Pass 4


ENDPOINT 3: POST /recommend/final
═══════════════════════════════════════════════════════════════════════════
Executes Pass 6: Portfolio Construction (depends on Pass 5)

Input:
  {
    "target_date": "DD-MM-YYYY",           (required)
    "investor_type": "Conservative|Balanced|Aggressive"  (required)
  }

Output (200 OK):
  {
    "status": "success",
    "stage": "pass6",
    "target_date": "01-04-2009",
    "investor_type": "Balanced",
    "message": "Pass 6 (Portfolio Construction) completed successfully...",
    "data": {
      "portfolio": {
        "VTV": 0.35,    (Value ETF)
        "QUAL": 0.35,   (Quality ETF)
        "MTUM": 0.30    (Momentum ETF)
      }
    }
  }

Error Responses: Similar structure to Pass 4


UTILITY ENDPOINTS:
═══════════════════════════════════════════════════════════════════════════

GET /
  Returns API information and pipeline overview

GET /health
  Returns {"status": "healthy", ...}
  Use this for monitoring/health checks

GET /api/pipeline
  Returns detailed documentation of all three stages
  Includes example flow and dependencies

GET /docs
  Swagger UI for interactive API testing
  
GET /redoc
  ReDoc for alternative API documentation
"""

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Complete Pipeline in Sequence
══════════════════════════════════════════════════════════════════════════

import requests
import json

BASE_URL = "http://localhost:10000"
DATE = "01-04-2009"

# Step 1: Regime Mapping
response1 = requests.post(
    f"{BASE_URL}/recommend/start",
    json={"target_date": DATE}
)
print("Pass 4:", response1.json()['message'])

# Step 2: Investor Allocation
response2 = requests.post(
    f"{BASE_URL}/recommend/investor",
    json={
        "target_date": DATE,
        "investor_type": "Balanced"
    }
)
print("Pass 5:", response2.json()['message'])

# Step 3: Portfolio Construction
response3 = requests.post(
    f"{BASE_URL}/recommend/final",
    json={
        "target_date": DATE,
        "investor_type": "Balanced"
    }
)
print("Pass 6:", response3.json()['message'])
portfolio = response3.json()['data']['portfolio']
print("Final Portfolio:", portfolio)


EXAMPLE 2: Using curl
══════════════════════════════════════════════════════════════════════════

# Start regime mapping
curl -X POST http://localhost:10000/recommend/start \
  -H "Content-Type: application/json" \
  -d '{"target_date": "01-04-2009"}'

# Run investor allocation
curl -X POST http://localhost:10000/recommend/investor \
  -H "Content-Type: application/json" \
  -d '{
    "target_date": "01-04-2009",
    "investor_type": "Balanced"
  }'

# Generate final portfolio
curl -X POST http://localhost:10000/recommend/final \
  -H "Content-Type: application/json" \
  -d '{
    "target_date": "01-04-2009",
    "investor_type": "Balanced"
  }'


EXAMPLE 3: Error Handling
══════════════════════════════════════════════════════════════════════════

import requests

response = requests.post(
    "http://localhost:10000/recommend/start",
    json={"target_date": "invalid-date"}
)

if response.status_code != 200:
    error = response.json()
    print(f"Error: {error['detail']}")
    # Output: "Error: Invalid date format: invalid-date. Expected DD-MM-YYYY"
"""

# ============================================================================
# SERVICE LAYER DETAILS
# ============================================================================

"""
SERVICES/PIPELINE.PY
═══════════════════════════════════════════════════════════════════════════

Exception Classes:
  - PipelineException: Base exception
  - Pass4ExecutionError: Pass 4 failed
  - Pass5ExecutionError: Pass 5 failed
  - Pass6ExecutionError: Pass 6 failed

Functions:
  
  run_pass4(target_date: str) -> Dict[str, Any]
    Executes: python Pass\ 4\ -\ Regime\ Mapping/outputs/pass4_regime_mapper.py \\
              --target-date {target_date}
    
    Returns: Loaded factor_tilt_latest.json
    Raises: Pass4ExecutionError on failure
    Timeout: 300 seconds
  
  run_pass5(target_date: str, investor_type: str) -> Dict[str, Any]
    Executes: python Pass\ 5\ -\ Portfolio\ Scoring/pass5_portfolioscorer.py \\
              --target-date {target_date} --investor-type {investor_type}
    
    Returns: Loaded portfolio_recommendation_latest.json
    Raises: Pass5ExecutionError on failure
    Timeout: 300 seconds
  
  run_pass6(target_date: str, investor_type: str) -> Dict[str, Any]
    Executes: python Pass\ 6\ -\ Portfolio\ Construction/pass6_portfolio_constructor.py \\
              --target-date {target_date} --investor-type {investor_type}
    
    Returns: Loaded portfolio_execution_latest.json
    Raises: Pass6ExecutionError on failure
    Timeout: 300 seconds

SERVICES/VALIDATION.PY
═══════════════════════════════════════════════════════════════════════════

Functions:

  validate_date_format(date_str: str) -> bool
    Checks if date is in DD-MM-YYYY format
    Returns True/False
  
  validate_investor_type(investor_type: str) -> bool
    Checks if investor type is one of: Conservative, Balanced, Aggressive
    Returns True/False
  
  validate_recommendation_request(target_date: str, investor_type: str) -> Tuple[bool, str]
    Comprehensive validation of both date and investor type
    Returns (is_valid, error_message)
"""

# ============================================================================
# ERROR HANDLING & HTTP STATUS CODES
# ============================================================================

"""
HTTP Status Codes:

200 OK
  ✓ All stages completed successfully
  Response includes: status, stage, data

400 Bad Request
  ✗ Input validation failed
  - Invalid date format
  - Invalid investor type
  - Missing required fields
  Response: {"detail": "..."}

422 Unprocessable Entity
  ✗ Pydantic validation error
  - Missing required field
  - Invalid field type
  Response: {"detail": [...]}

500 Internal Server Error
  ✗ Execution error during pipeline stage
  - Pass script failed (non-zero exit code)
  - Output file not created
  - Unexpected exception
  Response: {"detail": "..."}


DEBUGGING:

1. Check server logs for detailed error messages:
   tail -f logs/api.log

2. Run Pass scripts manually to test:
   cd "Pass 4 - Regime Mapping/outputs"
   python pass4_regime_mapper.py --target-date 01-04-2009

3. Verify output files exist after each stage:
   Pass 4: Pass 4 - Regime Mapping/outputs/factor_tilt_latest.json
   Pass 5: Pass 5 - Portfolio Scoring/outputs/portfolio_recommendation_latest.json
   Pass 6: Pass 6 - Portfolio Construction/outputs/portfolio_execution_latest.json

4. Test with curl before testing from frontend:
   curl http://localhost:10000/health
"""

# ============================================================================
# DEPLOYMENT
# ============================================================================

"""
LOCAL DEVELOPMENT:
  python api_server_refactored.py
  Server: http://localhost:10000

PRODUCTION WITH GUNICORN:
  pip install gunicorn
  
  gunicorn api_server_refactored:app \\
    --workers 4 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 0.0.0.0:10000 \\
    --timeout 300 \\
    --access-logfile - \\
    --error-logfile -

DOCKER:
  docker build -t macro-engine .
  docker run -p 10000:10000 macro-engine

RENDER / RAILWAY / CLOUD DEPLOYMENT:
  1. Ensure requirements.txt has all dependencies (should be up-to-date)
  2. Set start command to: python api_server_refactored.py
  3. Ensure PORT environment variable (if needed):
     PORT=${PORT:-10000} in app initialization
  4. Deploy via git push

ENVIRONMENT VARIABLES (Optional):
  WORKERS: Number of Gunicorn workers (default: 4)
  LOG_LEVEL: Logging level (default: info)
  TIMEOUT: Subprocess timeout (default: 300)
"""

# ============================================================================
# TESTING
# ============================================================================

"""
UNIT TESTS (if implemented):
  pytest tests/ -v

INTEGRATION TESTS:
  python test_api.py
  
  Tests:
  ✓ Health check
  ✓ Root endpoint
  ✓ Pipeline documentation
  ✓ Validation error handling
  ✓ Complete three-stage pipeline
  ✓ All investor types

MANUAL TESTING:
  1. Open http://localhost:10000/docs in browser
  2. Try each endpoint in the Swagger UI
  3. Check responses and error handling
"""

# ============================================================================
# CUSTOMIZATION GUIDE
# ============================================================================

"""
ADD A NEW INVESTOR TYPE:
  1. Edit services/validation.py
  2. Update validate_investor_type():
     valid_types = ["Conservative", "Balanced", "Aggressive", "Growth"]
  3. Update Pass 5 script to handle new type
  4. Restart API

ADD A NEW ENDPOINT:
  1. Create new file in routers/ (e.g., routers/analysis.py)
  2. Define router and endpoints
  3. Import and include in api_server_refactored.py:
     from routers.analysis import router as analysis_router
     app.include_router(analysis_router)
  4. Restart API

CHANGE DATE FORMAT:
  1. Edit services/validation.py, validate_date_format()
  2. Update pattern and strptime format
  3. Update documentation

CHANGE SUBPROCESS TIMEOUT:
  1. Edit services/pipeline.py, run_subprocess()
  2. Modify timeout parameter:
     result = subprocess.run(..., timeout=600)
  3. Restart API

ENABLE DEBUG LOGGING:
  1. Edit api_server_refactored.py
  2. Change logging level:
     logging.basicConfig(level=logging.DEBUG)
  3. Restart API
"""

# ============================================================================
# MIGRATION FROM OLD API
# ============================================================================

"""
The refactored API is a drop-in replacement for the old api_server.py.

OLD ENDPOINT                    →  NEW ENDPOINT
─────────────────────────────────────────────────────────────────────────
POST /recommend/start           →  POST /recommend/start (Pass 4 only)
GET /available-dates            →  Use /api/pipeline docs
POST /recommend                 →  POST /recommend/investor + POST /recommend/final

The new API is backwards compatible at the service level:
- Same input/output formats
- Same validation logic
- Same subprocess execution

Key differences:
+ Separate endpoints for each stage
+ Better error messages
+ Proper HTTP status codes
+ Type hints and validation
+ Comprehensive logging
+ Production-quality error handling
"""

print(__doc__)
