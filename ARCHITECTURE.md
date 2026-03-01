"""
ARCHITECTURAL DIAGRAM - Macro Engine API Pipeline

This document visualizes the refactored architecture and data flow.
"""

# ============================================================================
# SYSTEM ARCHITECTURE
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT / FRONTEND                               │
│                    (Web Browser / API Client)                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP Requests
                             ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       FASTAPI APPLICATION                               │
│              (api_server_refactored.py)                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Middleware Layer                                                │   │
│  │  • CORSMiddleware - Allow cross-origin requests                │   │
│  │  • Exception Handlers - Convert errors to HTTP responses       │   │
│  │  • Logging - Track all requests and errors                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             ↓                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Routing Layer (routers/recommendations.py)                       │   │
│  │                                                                   │   │
│  │  POST /recommend/start      POST /recommend/investor             │   │
│  │  POST /recommend/final      GET /health                          │   │
│  │  GET /api/pipeline          GET /docs                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             ↓                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Validation Layer (services/validation.py)                        │   │
│  │                                                                   │   │
│  │  • validate_date_format() - Check DD-MM-YYYY format             │   │
│  │  • validate_investor_type() - Check Conservative/Balanced/...   │   │
│  │  • validate_recommendation_request() - Full validation           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             ↓                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Pipeline Service Layer (services/pipeline.py)                    │   │
│  │                                                                   │   │
│  │  • run_pass4(target_date)                                        │   │
│  │  • run_pass5(target_date, investor_type)                        │   │
│  │  • run_pass6(target_date, investor_type)                        │   │
│  │  • run_subprocess() [helper]                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             ↓                                            │
└─────────────────────────────┬────────────────────────────────────────────┘
                             │ Subprocess Execution
                             ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    SUBPROCESS EXECUTION LAYER                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PASS 4: Regime Mapping                                           │   │
│  │ (Pass 4 - Regime Mapping/outputs/pass4_regime_mapper.py)        │   │
│  │                                                                   │   │
│  │ Input:   target_date (DD-MM-YYYY)                               │   │
│  │ Reads:   macro_data_scored.csv                                  │   │
│  │ Outputs: factor_tilt_latest.json                                │   │
│  │ Purpose: Detect regimes, generate factor weights                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PASS 5: Investor Allocation                                      │   │
│  │ (Pass 5 - Portfolio Scoring/pass5_portfolioscorer.py)           │   │
│  │                                                                   │   │
│  │ Input:   target_date, investor_type                             │   │
│  │ Reads:   factor_tilt_latest.json (from Pass 4)                 │   │
│  │          investor_profiles.json                                  │   │
│  │ Outputs: portfolio_recommendation_latest.json                   │   │
│  │ Purpose: Allocate portfolio based on investor type              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PASS 6: Portfolio Construction                                   │   │
│  │ (Pass 6 - Portfolio Construction/pass6_portfolio_constructor.py) │   │
│  │                                                                   │   │
│  │ Input:   target_date, investor_type                             │   │
│  │ Reads:   portfolio_recommendation_latest.json (from Pass 5)     │   │
│  │          asset_universe.json                                     │   │
│  │ Outputs: portfolio_execution_latest.json                        │   │
│  │ Purpose: Build final asset-level portfolio                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────┬──────────────────────────────────────────────┘
                          │ Output Files
                          ↓
         ┌────────────────────────────────────┐
         │  Pass 4 Output / Pass 5 Input       │
         │  factor_tilt_latest.json            │
         ├────────────────────────────────────┤
         │  Pass 5 Output / Pass 6 Input       │
         │  portfolio_recommendation_latest.json│
         ├────────────────────────────────────┤
         │  Pass 6 Output                      │
         │  portfolio_execution_latest.json    │
         └────────────────────────────────────┘
"""

# ============================================================================
# REQUEST-RESPONSE FLOW
# ============================================================================

"""
STAGE 1: POST /recommend/start
═══════════════════════════════════════════════════════════════════════════

Client Request:
  {
    "target_date": "01-04-2009"
  }
        ↓
Validation:
  ✓ Is target_date in DD-MM-YYYY format?
        ↓
Pipeline Service:
  • run_pass4("01-04-2009")
  • Execute: python pass4_regime_mapper.py --target-date 01-04-2009
  • Capture stdout, stderr, exit_code
  • Load factor_tilt_latest.json
        ↓
Response (200 OK):
  {
    "status": "success",
    "stage": "pass4",
    "target_date": "01-04-2009",
    "message": "Pass 4 (Regime Mapping) completed successfully.",
    "data": {
      "date": "01-04-2009",
      "active_regimes": ["High_Inflation", "Weak_Growth"],
      "factor_weights": {
        "Value": 0.4,
        "Quality": 0.3,
        "Momentum": 0.3
      }
    }
  }

Error Response (400 Bad Request):
  {
    "detail": "Invalid date format: 2009-04-01. Expected DD-MM-YYYY"
  }


STAGE 2: POST /recommend/investor
═══════════════════════════════════════════════════════════════════════════

Client Request:
  {
    "target_date": "01-04-2009",
    "investor_type": "Balanced"
  }
        ↓
Validation:
  ✓ Is target_date in DD-MM-YYYY format?
  ✓ Is investor_type one of: Conservative, Balanced, Aggressive?
        ↓
Pipeline Service:
  • run_pass5("01-04-2009", "Balanced")
  • Execute: python pass5_portfolioscorer.py --target-date 01-04-2009 --investor-type Balanced
  • Capture stdout, stderr, exit_code
  • Load portfolio_recommendation_latest.json
        ↓
Response (200 OK):
  {
    "status": "success",
    "stage": "pass5",
    "target_date": "01-04-2009",
    "investor_type": "Balanced",
    "message": "Pass 5 (Investor Allocation) completed successfully.",
    "data": {
      "investor_type": "Balanced",
      "portfolio_allocation": {
        "Value": 0.35,
        "Quality": 0.35,
        "Momentum": 0.30
      }
    }
  }

Error Response (500 Internal Server Error):
  {
    "detail": "Pass 5 failed: ModuleNotFoundError: No module named 'pandas'"
  }


STAGE 3: POST /recommend/final
═══════════════════════════════════════════════════════════════════════════

Client Request:
  {
    "target_date": "01-04-2009",
    "investor_type": "Balanced"
  }
        ↓
Validation:
  ✓ Is target_date in DD-MM-YYYY format?
  ✓ Is investor_type one of: Conservative, Balanced, Aggressive?
        ↓
Pipeline Service:
  • run_pass6("01-04-2009", "Balanced")
  • Execute: python pass6_portfolio_constructor.py --target-date 01-04-2009 --investor-type Balanced
  • Capture stdout, stderr, exit_code
  • Load portfolio_execution_latest.json
        ↓
Response (200 OK):
  {
    "status": "success",
    "stage": "pass6",
    "target_date": "01-04-2009",
    "investor_type": "Balanced",
    "message": "Pass 6 (Portfolio Construction) completed successfully.",
    "data": {
      "portfolio": {
        "VTV": 0.35,
        "QUAL": 0.35,
        "MTUM": 0.30
      }
    }
  }

Error Response (500 Internal Server Error):
  {
    "detail": "Pass 6 failed: FileNotFoundError: portfolio_recommendation_latest.json"
  }
"""

# ============================================================================
# FILE ORGANIZATION
# ============================================================================

"""
Project Root/
│
├── api_server_refactored.py          [Main App]
│   └── Creates FastAPI app, includes routers, sets up middleware
│
├── services/
│   ├── __init__.py
│   ├── pipeline.py                   [Business Logic]
│   │   ├── run_pass4()
│   │   ├── run_pass5()
│   │   ├── run_pass6()
│   │   ├── run_subprocess() [Helper]
│   │   └── Custom Exceptions
│   │
│   └── validation.py                 [Input Validation]
│       ├── validate_date_format()
│       ├── validate_investor_type()
│       └── validate_recommendation_request()
│
├── routers/
│   ├── __init__.py
│   └── recommendations.py            [API Endpoints]
│       ├── POST /recommend/start
│       ├── POST /recommend/investor
│       ├── POST /recommend/final
│       └── Pydantic Models
│
├── Pass 4 - Regime Mapping/
│   └── outputs/
│       ├── pass4_regime_mapper.py
│       └── [outputs: factor_tilt_latest.json]
│
├── Pass 5 - Portfolio Scoring/
│   ├── pass5_portfolioscorer.py
│   └── outputs/
│       └── [outputs: portfolio_recommendation_latest.json]
│
├── Pass 6 - Portfolio Construction/
│   ├── pass6_portfolio_constructor.py
│   └── outputs/
│       └── [outputs: portfolio_execution_latest.json]
│
├── web/
│   └── [static files, can be served via FastAPI]
│
├── logs/
│   └── api.log                       [Logging output]
│
├── test_api.py                       [Integration Tests]
├── start_api_refactored.sh           [Startup Script]
├── requirements.txt                  [Dependencies]
│
└── Documentation/
    ├── API_README.py                 [API Reference]
    ├── REFACTORING_GUIDE.md          [Technical Guide]
    ├── REFACTORING_SUMMARY.md        [What Changed]
    ├── REFACTORING_COMPLETE.md       [Full Summary]
    └── ARCHITECTURE.md               [This File]
"""

# ============================================================================
# DEPENDENCY GRAPH
# ============================================================================

"""
PASS DEPENDENCIES:
═════════════════════════════════════════════════════════════════════════

Pass 4 (Regime Mapping)
  ├─ Input: target_date
  ├─ Dependencies: None
  └─ Output: factor_tilt_latest.json
          │
          ↓
Pass 5 (Investor Allocation)
  ├─ Input: target_date, investor_type
  ├─ Dependencies: Pass 4 output (factor_tilt_latest.json)
  └─ Output: portfolio_recommendation_latest.json
          │
          ↓
Pass 6 (Portfolio Construction)
  ├─ Input: target_date, investor_type
  ├─ Dependencies: Pass 5 output (portfolio_recommendation_latest.json)
  └─ Output: portfolio_execution_latest.json


DATA FLOW:
═════════════════════════════════════════════════════════════════════════

Client
  ↓
Pass 4: Reads macro_data_scored.csv → Outputs factor_tilt_latest.json
  ↓
Pass 5: Reads factor_tilt_latest.json + investor_profiles.json 
        → Outputs portfolio_recommendation_latest.json
  ↓
Pass 6: Reads portfolio_recommendation_latest.json + asset_universe.json
        → Outputs portfolio_execution_latest.json
  ↓
Client Gets Final Portfolio
"""

# ============================================================================
# ERROR HANDLING FLOW
# ============================================================================

"""
REQUEST HANDLING WITH ERROR HANDLING:
═════════════════════════════════════════════════════════════════════════

Request Arrives
    ↓
Pydantic Validation
    ├─ 422 Unprocessable Entity (missing/invalid field)
    └─ OK (Field present and correct type)
            ↓
Input Validation Service
    ├─ 400 Bad Request (date format wrong, investor type invalid)
    └─ OK (All validation passed)
            ↓
Pipeline Service
    ├─ 500 Internal Server Error
    │  ├─ Subprocess timed out (>300s)
    │  ├─ Subprocess exit code non-zero
    │  ├─ Output file not found
    │  └─ Unexpected exception
    └─ OK (Subprocess succeeded, output loaded)
            ↓
Response Builder
    └─ 200 OK + JSON Response


HTTP STATUS CODES:
═════════════════════════════════════════════════════════════════════════

200 OK
  ✓ Everything succeeded
  Response: {status: "success", stage: "...", data: {...}}

400 Bad Request
  ✗ Input validation failed
  Response: {detail: "..."}

422 Unprocessable Entity
  ✗ Pydantic validation failed (missing/invalid field)
  Response: {detail: [...]}

500 Internal Server Error
  ✗ Pipeline execution failed
  Response: {detail: "..."}
"""

# ============================================================================
# SCALING & CONCURRENCY
# ============================================================================

"""
CONCURRENT REQUEST HANDLING:
═════════════════════════════════════════════════════════════════════════

With async endpoints and Gunicorn workers:

Client 1
  ├─→ Worker 1: Request 1
  │    └─→ Async handling (non-blocking I/O during subprocess)
  └─→ Returns response

Client 2
  ├─→ Worker 2: Request 2
  │    └─→ Async handling
  └─→ Returns response

Client 3
  ├─→ Worker 3: Request 3
  └─→ Returns response

Multiple clients can be served simultaneously by multiple Gunicorn workers.
Each worker handles async endpoints efficiently.


RECOMMENDED DEPLOYMENT:
═════════════════════════════════════════════════════════════════════════

gunicorn api_server_refactored:app \\
  --workers 4 \\
  --worker-class uvicorn.workers.UvicornWorker \\
  --bind 0.0.0.0:10000 \\
  --timeout 300

This allows up to 4 concurrent Uvicorn workers, each handling async requests.
"""

print(__doc__)
