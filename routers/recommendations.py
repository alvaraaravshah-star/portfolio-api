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
router = APIRouter(prefix="/recommend")


# ---------- models ---------------------------------------------------------
class RecommendStartRequest(BaseModel):
    target_date: str = Field(..., description="YYYY-DD-MM")


class RecommendStartResponse(BaseModel):
    status: str
    stage: str
    target_date: str
    message: str
    data: Dict[str, Any]


class RecommendInvestorRequest(BaseModel):
    target_date: str = Field(..., description="YYYY-DD-MM")
    investor_type: str = Field(..., description="Conservative|Balanced|Aggressive")


class RecommendInvestorResponse(BaseModel):
    status: str
    stage: str
    target_date: str
    investor_type: str
    message: str
    data: Dict[str, Any]


class RecommendFinalRequest(BaseModel):
    target_date: str = Field(..., description="YYYY-DD-MM")
    investor_type: str = Field(..., description="Conservative|Balanced|Aggressive")


class RecommendFinalResponse(BaseModel):
    status: str
    stage: str
    target_date: str
    investor_type: str
    message: str
    data: Dict[str, Any]


class ErrorResponse(BaseModel):
    status: str
    stage: str
    error: str
    details: str = ""


# ---------- endpoints ------------------------------------------------------
@router.post(
    "/start",
    response_model=RecommendStartResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def recommend_start(request: RecommendStartRequest) -> RecommendStartResponse:
    logger.info("recommend_start received %s", request.target_date)

    valid, err = validate_recommendation_request(request.target_date, "Balanced")
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    try:
        logger.info("running Pass 4 for %s", request.target_date)
        result = run_pass4(request.target_date)
        logger.info("Pass 4 completed")

        return RecommendStartResponse(
            status="success",
            stage="pass4",
            target_date=request.target_date,
            message="Pass 4 completed",
            data=result,
        )

    except Pass4ExecutionError as e:
        logger.error("Pass 4 error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error("Unexpected Pass 4 error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/investor",
    response_model=RecommendInvestorResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def recommend_investor(request: RecommendInvestorRequest) -> RecommendInvestorResponse:
    logger.info("recommend_investor %s %s", request.target_date, request.investor_type)

    valid, err = validate_recommendation_request(request.target_date, request.investor_type)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    try:
        logger.info("running Pass 5 for %s %s", request.target_date, request.investor_type)
        result = run_pass5(request.target_date, request.investor_type)
        logger.info("Pass 5 completed")

        return RecommendInvestorResponse(
            status="success",
            stage="pass5",
            target_date=request.target_date,
            investor_type=request.investor_type,
            message="Pass 5 completed",
            data=result,
        )

    except Pass5ExecutionError as e:
        logger.error("Pass 5 error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error("Unexpected Pass 5 error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/final",
    response_model=RecommendFinalResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def recommend_final(request: RecommendFinalRequest) -> RecommendFinalResponse:
    logger.info("recommend_final %s %s", request.target_date, request.investor_type)

    valid, err = validate_recommendation_request(request.target_date, request.investor_type)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    try:
        logger.info("running Pass 6 for %s %s", request.target_date, request.investor_type)
        result = run_pass6(request.target_date, request.investor_type)
        logger.info("Pass 6 completed")

        return RecommendFinalResponse(
            status="success",
            stage="pass6",
            target_date=request.target_date,
            investor_type=request.investor_type,
            message="Pass 6 completed",
            data=result,
        )

    except Pass6ExecutionError as e:
        logger.error("Pass 6 error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error("Unexpected Pass 6 error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

