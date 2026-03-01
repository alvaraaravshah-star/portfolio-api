from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Set, Tuple
from datetime import datetime
import subprocess
import sys
import logging
import re

# -----------------------------------------------------------------------------
# logging configuration
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# utility/validation helpers
# -----------------------------------------------------------------------------

def validate_date_format(date_str: str) -> bool:
    """Return True if the string is a valid YYYY-DD-MM date.

    We check a simple regex then attempt to parse it with datetime so that
    obviously invalid dates (e.g. 2020-31-02) are rejected.
    """
    if not isinstance(date_str, str):
        return False
    pattern = r"^\d{4}-\d{2}-\d{2}$"  # year-day-month
    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%d-%m")
        return True
    except ValueError:
        return False


def validate_investor_type(investor_type: str) -> bool:
    return investor_type in {"Conservative", "Balanced", "Aggressive"}

# this state keeps track of which dates have successfully completed each
# stage.  in a real application this would be persisted to a database.
_pass4_done: Set[str] = set()
_pass5_done: Set[Tuple[str, str]] = set()

# -----------------------------------------------------------------------------
# subprocess helpers
# -----------------------------------------------------------------------------

def run_pass4(target_date: str) -> None:
    """Execute pass4_regime_mapper.py and raise HTTPException on failure.

    The script is expected to accept a single command‑line argument which is
    the date (YYYY-DD-MM). This helper does *not* return any data; the caller
    can read files written by the script if necessary.
    """
    script = Path(__file__).parent / "Pass 4 - Regime Mapping" / "outputs" / "pass4_regime_mapper.py"
    logger.info("running Pass 4 for date %s", target_date)
    try:
        subprocess.run([sys.executable, str(script), target_date], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Pass 4 failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Pass 4 failed for {target_date}")


def run_pass5(target_date: str, investor_type: str) -> None:
    """Execute pass5_investor_allocator.py; depends on Pass 4 success.
    """
    if target_date not in _pass4_done:
        raise HTTPException(status_code=400, detail="Pass 4 must succeed before Pass 5")
    script = Path(__file__).parent / "Pass 5 - Portfolio Scoring" / "pass5_investor_allocator.py"
    logger.info("running Pass 5 for date %s investor %s", target_date, investor_type)
    try:
        subprocess.run([sys.executable, str(script), "--target-date", target_date, "--investor-type", investor_type], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Pass 5 failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Pass 5 failed for {target_date} / {investor_type}")


def run_pass6(target_date: str, investor_type: str) -> dict:
    """Execute pass6_output_generator.py; depends on Pass 5 success.

    Returns the JSON produced by the script on stdout or via a known file.
    """
    if (target_date, investor_type) not in _pass5_done:
        raise HTTPException(status_code=400, detail="Pass 5 must succeed before Pass 6")
    script = Path(__file__).parent / "Pass 6 - Portfolio Construction" / "pass6_output_generator.py"
    logger.info("running Pass 6 for date %s investor %s", target_date, investor_type)
    try:
        result = subprocess.run([sys.executable, str(script), "--target-date", target_date, "--investor-type", investor_type], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Pass 6 failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Pass 6 failed for {target_date} / {investor_type}")
    except Exception as e:
        logger.error("unable to parse Pass 6 output: %s", e)
        raise HTTPException(status_code=500, detail="Pass 6 produced invalid JSON")

# -----------------------------------------------------------------------------
# Pydantic models for requests/responses
# -----------------------------------------------------------------------------

class StartRequest(BaseModel):
    target_date: str = Field(..., description="Target date in YYYY-DD-MM format")

class StageResponse(BaseModel):
    status: str
    message: str

class FinalResponse(BaseModel):
    status: str
    recommendation: dict

# -----------------------------------------------------------------------------
# API router and endpoints
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/recommend", tags=["recommend"])

@router.post("/start", response_model=StageResponse)
async def recommend_start(req: StartRequest):
    # validate input
    if not validate_date_format(req.target_date):
        raise HTTPException(status_code=400, detail="invalid date format")
    # run Pass 4
    run_pass4(req.target_date)
    _pass4_done.add(req.target_date)
    return {"status": "success", "message": "Pass 4 completed"}

@router.post("/investor", response_model=StageResponse)
async def recommend_investor(req: StartRequest, investor_type: str = Field(...)):
    if not validate_date_format(req.target_date):
        raise HTTPException(status_code=400, detail="invalid date format")
    if not validate_investor_type(investor_type):
        raise HTTPException(status_code=400, detail="invalid investor_type")
    run_pass5(req.target_date, investor_type)
    _pass5_done.add((req.target_date, investor_type))
    return {"status": "success", "message": "Pass 5 completed"}

@router.post("/final", response_model=FinalResponse)
async def recommend_final(req: StartRequest, investor_type: str = Field(...)):
    if not validate_date_format(req.target_date):
        raise HTTPException(status_code=400, detail="invalid date format")
    if not validate_investor_type(investor_type):
        raise HTTPException(status_code=400, detail="invalid investor_type")
    rec = run_pass6(req.target_date, investor_type)
    return {"status": "success", "recommendation": rec}

# -----------------------------------------------------------------------------
# application entrypoint
# -----------------------------------------------------------------------------

app = FastAPI(title="Multi‑Stage Recommendation API")
app.include_router(router)

# optional health check
@app.get("/health")
async def health():
    return {"status": "healthy"}
