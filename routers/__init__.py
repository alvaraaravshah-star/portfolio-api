"""
Recommendation Router
Handles endpoints for the multi-stage recommendation pipeline.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.pipeline import (
    run_pass4,
    run_pass5,
    run_pass6,
    Pass4ExecutionError,
    Pass5ExecutionError,
    Pass6ExecutionError,
)
from services.validation import validate_recommendation_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommendations"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RecommendStartRequest(BaseModel):
    """Request for starting Pass 4 (Regime Mapping)."""
    target_date: str = Field(
        ...,
        description="Target date in DD-MM-YYYY format (e.g., '01-04-2009')"
    )


class RecommendStartResponse(BaseModel):
    """Response from Pass 4 execution."""
    status: str = "success"
    stage: str = "pass4"
    target_date: str
    message: str
    data: Dict[str, Any] = Field(description="Pass 4 regime mapping output")


class RecommendInvestorRequest(BaseModel):
    """Request for Pass 5 (Investor Allocation)."""
    target_date: str = Field(
        ...,
        description="Target date in DD-MM-YYYY format (e.g., '01-04-2009')"
    )
    investor_type: str = Field(
        ...,
        description="Investor profile type: Conservative, Balanced, or Aggressive"
    )


class RecommendInvestorResponse(BaseModel):
    """Response from Pass 5 execution."""
    status: str = "success"
    stage: str = "pass5"
    target_date: str
    investor_type: str
    message: str
    data: Dict[str, Any] = Field(description="Pass 5 portfolio scoring output")


class RecommendFinalRequest(BaseModel):
    """Request for Pass 6 (Final Output)."""
    target_date: str = Field(
        ...,
        description="Target date in DD-MM-YYYY format (e.g., '01-04-2009')"
    )
    investor_type: str = Field(
        ...,
        description="Investor profile type: Conservative, Balanced, or Aggressive"
    )


class RecommendFinalResponse(BaseModel):
    """Response from Pass 6 execution."""
    status: str = "success"
    stage: str = "pass6"
    target_date: str
    investor_type: str
    message: str
    data: Dict[str, Any] = Field(description="Pass 6 portfolio execution output")


class ErrorResponse(BaseModel):
    """Error response."""
    status: str = "error"
    stage: str
    error: str
    details: str = ""


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/start",
    response_model=RecommendStartResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Start recommendation pipeline - Pass 4 (Regime Mapping)",
    description="Execute Pass 4 to map market regime for a target date."
)
async def recommend_start(request: RecommendStartRequest) -> RecommendStartResponse:
    """
    POST /recommend/start
    
    Start the recommendation pipeline by executing Pass 4 (Regime Mapping).
    
    This stage:
    - Takes a target date
    - Detects active market regimes
    - Generates factor tilts based on regimes
    - Produces Pass 4 output required for Pass 5
    
    Args:
        request: RecommendStartRequest with target_date
    
    Returns:
        RecommendStartResponse with regime mapping data
    
    Raises:
        HTTPException: If validation or execution fails
    """
    logger.info(f"Recommend.start: Received request for date {request.target_date}")
    
    # Validate input
    is_valid, error_msg = validate_recommendation_request(request.target_date, "Balanced")
    if not is_valid:
        logger.warning(f"Recommend.start: Validation failed - {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        logger.info(f"Recommend.start: Executing Pass 4 for date {request.target_date}")
        pass4_result = run_pass4(request.target_date)
        
        logger.info(f"Recommend.start: Pass 4 completed successfully")
        
        return RecommendStartResponse(
            status="success",
            stage="pass4",
            target_date=request.target_date,
            message="Pass 4 (Regime Mapping) completed successfully. Proceed to Pass 5 (Investor Allocation).",
            data=pass4_result
        )
    
    except Pass4ExecutionError as e:
        logger.error(f"Recommend.start: Pass 4 execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pass 4 failed: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Recommend.start: Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during Pass 4: {str(e)}"
        )


@router.post(
    "/investor",
    response_model=RecommendInvestorResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Execute Pass 5 (Investor Allocation)",
    description="Allocate portfolio based on investor type. Requires Pass 4 to be completed first."
)
async def recommend_investor(request: RecommendInvestorRequest) -> RecommendInvestorResponse:
    """
    POST /recommend/investor
    
    Execute Pass 5 (Investor Allocation).
    
    This stage depends on Pass 4 output and:
    - Takes target date and investor type
    - Allocates factors based on investor profile
    - Generates portfolio recommendations
    - Produces Pass 5 output required for Pass 6
    
    Args:
        request: RecommendInvestorRequest with target_date and investor_type
    
    Returns:
        RecommendInvestorResponse with portfolio scoring data
    
    Raises:
        HTTPException: If validation, Pass 4 output missing, or execution fails
    """
    logger.info(f"Recommend.investor: Received request for date {request.target_date}, investor {request.investor_type}")
    
    # Validate input
    is_valid, error_msg = validate_recommendation_request(request.target_date, request.investor_type)
    if not is_valid:
        logger.warning(f"Recommend.investor: Validation failed - {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        logger.info(f"Recommend.investor: Executing Pass 5")
        pass5_result = run_pass5(request.target_date, request.investor_type)
        
        logger.info(f"Recommend.investor: Pass 5 completed successfully")
        
        return RecommendInvestorResponse(
            status="success",
            stage="pass5",
            target_date=request.target_date,
            investor_type=request.investor_type,
            message=f"Pass 5 (Investor Allocation) completed successfully for {request.investor_type} investor. Proceed to Pass 6 (Portfolio Construction).",
            data=pass5_result
        )
    
    except Pass5ExecutionError as e:
        logger.error(f"Recommend.investor: Pass 5 execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pass 5 failed: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Recommend.investor: Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during Pass 5: {str(e)}"
        )


@router.post(
    "/final",
    response_model=RecommendFinalResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Execute Pass 6 (Portfolio Construction) - Final Output",
    description="Generate final portfolio execution plan. Requires Pass 5 to be completed first."
)
async def recommend_final(request: RecommendFinalRequest) -> RecommendFinalResponse:
    """
    POST /recommend/final
    
    Execute Pass 6 (Portfolio Construction) to generate final output.
    
    This stage depends on Pass 5 output and:
    - Takes target date and investor type
    - Constructs final portfolio with asset-level allocations
    - Generates execution-ready output
    - Returns complete recommendation to client
    
    Args:
        request: RecommendFinalRequest with target_date and investor_type
    
    Returns:
        RecommendFinalResponse with final portfolio execution data
    
    Raises:
        HTTPException: If validation, Pass 5 output missing, or execution fails
    """
    logger.info(f"Recommend.final: Received request for date {request.target_date}, investor {request.investor_type}")
    
    # Validate input
    is_valid, error_msg = validate_recommendation_request(request.target_date, request.investor_type)
    if not is_valid:
        logger.warning(f"Recommend.final: Validation failed - {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        logger.info(f"Recommend.final: Executing Pass 6")
        pass6_result = run_pass6(request.target_date, request.investor_type)
        
        logger.info(f"Recommend.final: Pass 6 completed successfully")
        
        return RecommendFinalResponse(
            status="success",
            stage="pass6",
            target_date=request.target_date,
            investor_type=request.investor_type,
            message=f"Pass 6 (Portfolio Construction) completed successfully. Final portfolio recommendation ready.",
            data=pass6_result
        )
    
    except Pass6ExecutionError as e:
        logger.error(f"Recommend.final: Pass 6 execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pass 6 failed: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Recommend.final: Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during Pass 6: {str(e)}"
        )
