"""
FastAPI server for the Macro Engine Interactive Application
Integrates Pass 4 (Regime Mapping), Pass 5 (Portfolio Scoring), and Pass 6 (Portfolio Construction)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(
    title="Macro Engine API",
    description="API for regime-based portfolio construction",
    version="1.0.0"
)

# Get base directory
BASE_DIR = Path(__file__).parent

# Define paths to data files
PASS4_DATA_PATH = BASE_DIR / "Pass 4 - Regime Mapping" / "outputs" / "factor_tilt_latest.json"
PASS5_DATA_PATH = BASE_DIR / "Pass 5 - Portfolio Scoring" / "investor_profiles.json"
PASS6_DATA_PATH = BASE_DIR / "Pass 6 - Portfolio Construction" / "outputs" / "portfolio_execution_latest.json"

# Pydantic models for request/response
class PortfolioRequest(BaseModel):
    """Request model for portfolio recommendation"""
    target_date: str = Field(..., description="Target date from Pass 4 (e.g., '01-04-2009')")
    investor_type: str = Field(
        ...,
        description="Investor type from Pass 5 (Conservative, Balanced, or Aggressive)"
    )

class RegimeData(BaseModel):
    """Response model for Pass 4 regime data"""
    date: str
    active_regimes: list[str]
    regime_strength: dict
    factor_weights: dict

class InvestorProfile(BaseModel):
    """Response model for investor profile"""
    preferred_factors: list[str]
    macro_weight: float
    investor_weight: float

class PortfolioRecommendation(BaseModel):
    """Response model for portfolio recommendation"""
    metadata: dict
    portfolio: dict
    explanation: dict
    regime_data: RegimeData
    investor_profile: InvestorProfile

# Utility functions
def load_json_file(filepath: Path) -> dict:
    """Load and parse a JSON file"""
    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Data file not found: {filepath}"
        )
    with open(filepath, 'r') as f:
        return json.load(f)

def get_available_dates() -> list[str]:
    """Get list of available dates from Pass 4 outputs"""
    # For now, we'll return the date from the latest file
    # In production, you might want to scan a directory for multiple dates
    try:
        data = load_json_file(PASS4_DATA_PATH)
        return [data.get("date", "01-04-2009")]
    except:
        return ["01-04-2009"]

def get_available_investor_types() -> list[str]:
    """Get list of available investor types from Pass 5"""
    try:
        data = load_json_file(PASS5_DATA_PATH)
        return list(data.keys())
    except:
        return ["Conservative", "Balanced", "Aggressive"]

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "title": "Macro Engine API",
        "description": "Portfolio recommendation engine integrating regime analysis",
        "endpoints": {
            "available_dates": "/available-dates",
            "available_investor_types": "/available-investor-types",
            "recommend": "/recommend"
        },
        "example_request": {
            "target_date": "01-04-2009",
            "investor_type": "Balanced"
        }
    }

@app.get("/available-dates")
async def available_dates():
    """Get list of available dates from Pass 4"""
    try:
        dates = get_available_dates()
        return {
            "dates": dates,
            "count": len(dates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/available-investor-types")
async def available_investor_types():
    """Get list of available investor types from Pass 5"""
    try:
        types = get_available_investor_types()
        return {
            "investor_types": types,
            "count": len(types)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend")
async def get_recommendation(request: PortfolioRequest) -> PortfolioRecommendation:
    """
    Get portfolio recommendation based on target date and investor type
    
    Integrates:
    - Pass 4: Regime data for the target date
    - Pass 5: Investor profile preferences
    - Pass 6: Portfolio construction output
    """
    try:
        # Load all necessary data
        pass4_data = load_json_file(PASS4_DATA_PATH)
        pass5_data = load_json_file(PASS5_DATA_PATH)
        pass6_data = load_json_file(PASS6_DATA_PATH)
        
        # Validate inputs
        available_investor_types = list(pass5_data.keys())
        if request.investor_type not in available_investor_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid investor_type. Must be one of: {available_investor_types}"
            )
        
        # Validate target date matches available data (simplified check)
        if request.target_date != pass4_data.get("date"):
            # For now, we warn but still proceed with the available data
            pass
        
        # Extract investor profile
        investor_profile = pass5_data[request.investor_type]
        
        # Build response
        response = {
            "metadata": pass6_data.get("metadata", {}),
            "portfolio": pass6_data.get("portfolio", {}),
            "explanation": pass6_data.get("explanation", {}),
            "regime_data": {
                "date": pass4_data.get("date"),
                "active_regimes": pass4_data.get("active_regimes", []),
                "regime_strength": pass4_data.get("regime_strength", {}),
                "factor_weights": pass4_data.get("factor_weights", {})
            },
            "investor_profile": {
                "preferred_factors": investor_profile.get("preferred_factors", []),
                "macro_weight": investor_profile.get("macro_weight", 0),
                "investor_weight": investor_profile.get("investor_weight", 0)
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")

@app.get("/regime-data")
async def get_regime_data(target_date: Optional[str] = Query(None)):
    """Get regime data from Pass 4"""
    try:
        data = load_json_file(PASS4_DATA_PATH)
        if target_date and data.get("date") != target_date:
            return {"warning": "Requested date not available", "available_date": data.get("date")}
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio-execution")
async def get_portfolio_execution():
    """Get portfolio execution output from Pass 6"""
    try:
        data = load_json_file(PASS6_DATA_PATH)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_files": {
            "pass4": PASS4_DATA_PATH.exists(),
            "pass5": PASS5_DATA_PATH.exists(),
            "pass6": PASS6_DATA_PATH.exists()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
