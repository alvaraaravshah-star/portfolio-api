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
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(
    title="Macro Engine API",
    description="API for regime-based portfolio construction",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to specific domain: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory
BASE_DIR = Path(__file__).parent

# Mount static files (web UI)
WEB_DIR = BASE_DIR / "web"
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

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
async def get_recommendation(request: PortfolioRequest):
    """
    Get portfolio recommendation based on target date and investor type.
    Uses actual Pass 5 + Pass 6 logic to generate dynamic recommendations.
    
    Flow:
    1. Load Pass 4 regime data
    2. Load Pass 5 investor profiles and candidate portfolios
    3. Score portfolios based on macro regime + investor type
    4. Select best portfolio and construct assets via Pass 6
    5. Return complete recommendation
    """
    try:
        # Load all necessary data
        pass4_data = load_json_file(PASS4_DATA_PATH)
        pass5_data = load_json_file(PASS5_DATA_PATH)
        
        # Load Pass 5 candidate portfolios
        pass5_portfolios_path = BASE_DIR / "Pass 5 - Portfolio Scoring" / "candidate_portfolios.json"
        if pass5_portfolios_path.exists():
            with open(pass5_portfolios_path, 'r') as f:
                candidate_portfolios = json.load(f)
        else:
            candidate_portfolios = {}
        
        # Load Pass 6 asset universe
        asset_universe_path = BASE_DIR / "Pass 6 - Portfolio Construction" / "asset_universe.json"
        if asset_universe_path.exists():
            with open(asset_universe_path, 'r') as f:
                asset_universe = json.load(f)
        else:
            asset_universe = {}
        
        # Validate inputs
        available_investor_types = list(pass5_data.keys())
        if request.investor_type not in available_investor_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid investor_type. Must be one of: {available_investor_types}"
            )
        
        # Get investor profile
        investor_profile = pass5_data[request.investor_type]
        preferred_factors = investor_profile.get("preferred_factors", [])
        macro_weight = investor_profile.get("macro_weight", 0.5)
        investor_weight = investor_profile.get("investor_weight", 0.5)
        
        # Get macro factor weights from Pass 4
        macro_factor_weights = pass4_data.get("factor_weights", {})
        
        # Pass 5 Logic: Score portfolios based on macro + investor alignment
        best_portfolio_name = None
        best_portfolio_score = -1
        portfolio_scores = {}
        
        for portfolio_name, portfolio_data in candidate_portfolios.items():
            portfolio_factors = portfolio_data.get("factors", {})
            
            # Calculate macro score: how well portfolio aligns with regime factors
            macro_score = 0
            for factor, macro_weight_val in macro_factor_weights.items():
                if factor in portfolio_factors:
                    macro_score += macro_weight_val * portfolio_factors[factor]
            
            # Calculate investor score: how well portfolio aligns with investor preferences
            investor_score = 0
            for factor in preferred_factors:
                if factor in portfolio_factors:
                    investor_score += portfolio_factors[factor]
            investor_score = investor_score / max(len(preferred_factors), 1)  # Normalize
            
            # Weighted composite score
            composite_score = (macro_weight * macro_score) + (investor_weight * investor_score)
            portfolio_scores[portfolio_name] = {
                "macro_score": macro_score,
                "investor_score": investor_score,
                "composite_score": composite_score
            }
            
            if composite_score > best_portfolio_score:
                best_portfolio_score = composite_score
                best_portfolio_name = portfolio_name
        
        # If no portfolios found, use first available or default
        if best_portfolio_name is None:
            best_portfolio_name = list(candidate_portfolios.keys())[0] if candidate_portfolios else "Balanced"
        
        selected_portfolio = candidate_portfolios.get(best_portfolio_name, {})
        portfolio_factors = selected_portfolio.get("factors", macro_factor_weights)
        
        # Pass 6 Logic: Map factors to ETFs and construct asset allocation
        asset_allocation = {}
        factor_to_etf = {}
        
        for factor, weight in portfolio_factors.items():
            # Select first ETF available for this factor
            if factor in asset_universe and asset_universe[factor]:
                selected_etf = asset_universe[factor][0]
            else:
                selected_etf = factor  # Fallback to factor name
            
            factor_to_etf[factor] = selected_etf
            asset_allocation[selected_etf] = asset_allocation.get(selected_etf, 0) + weight
        
        # Normalize weights to sum to 1
        total_weight = sum(asset_allocation.values())
        if total_weight > 0:
            asset_allocation = {etf: w / total_weight for etf, w in asset_allocation.items()}
        
        # Build response
        response = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "requested_investor_type": request.investor_type,
                "target_date": request.target_date,
                "selected_portfolio": best_portfolio_name,
                "portfolio_score": float(best_portfolio_score)
            },
            "portfolio": {
                "name": best_portfolio_name,
                "assets": asset_allocation,
                "factor_weights": portfolio_factors
            },
            "portfolio_scores": portfolio_scores,
            "explanation": {
                "macro": f"Macro regime has factor weights: {macro_factor_weights}",
                "investor": f"{request.investor_type} investor prefers: {', '.join(preferred_factors)}",
                "construction": f"Portfolio '{best_portfolio_name}' selected with composite score {best_portfolio_score:.3f}. Factors mapped to ETFs: {factor_to_etf}"
            },
            "regime_data": {
                "date": pass4_data.get("date"),
                "active_regimes": pass4_data.get("active_regimes", []),
                "regime_strength": pass4_data.get("regime_strength", {}),
                "factor_weights": macro_factor_weights
            },
            "investor_profile": {
                "preferred_factors": preferred_factors,
                "macro_weight": macro_weight,
                "investor_weight": investor_weight
            },
            "factor_to_etf_mapping": factor_to_etf
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
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
