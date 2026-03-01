"""
Pipeline Service Module
Handles execution of Pass 4, 5, and 6 scripts with proper error handling and logging.
"""

import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class PipelineException(Exception):
    """Base exception for pipeline execution errors."""
    pass


class Pass4ExecutionError(PipelineException):
    """Pass 4 (Regime Mapping) execution error."""
    pass


class Pass5ExecutionError(PipelineException):
    """Pass 5 (Investor Allocation) execution error."""
    pass


class Pass6ExecutionError(PipelineException):
    """Pass 6 (Final Output Generation) execution error."""
    pass


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def run_subprocess(
    script_path: Path,
    args: list[str],
    stage: str,
    timeout: int = 300
) -> Tuple[int, str, str]:
    """
    Execute a subprocess and capture output.
    
    Args:
        script_path: Path to the Python script to execute
        args: Command-line arguments to pass to the script
        stage: Stage name (for logging)
        timeout: Maximum execution time in seconds
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    
    Raises:
        PipelineException: If the subprocess fails
    """
    if not script_path.exists():
        raise PipelineException(f"{stage}: Script not found at {script_path}")
    
    # Build command
    command = ["python", str(script_path)] + args
    
    logger.info(f"{stage}: Starting execution with command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(get_project_root())
        )
        
        logger.info(f"{stage}: Exit code {result.returncode}")
        
        if result.stdout:
            logger.debug(f"{stage} stdout: {result.stdout[:500]}")  # Log first 500 chars
        if result.stderr:
            logger.warning(f"{stage} stderr: {result.stderr[:500]}")
        
        return result.returncode, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        logger.error(f"{stage}: Timeout after {timeout} seconds")
        raise PipelineException(f"{stage}: Execution timeout (>{timeout}s)")
    
    except Exception as e:
        logger.error(f"{stage}: Unexpected error: {str(e)}")
        raise PipelineException(f"{stage}: {str(e)}")


def run_pass4(target_date: str) -> Dict[str, Any]:
    """
    Execute Pass 4 (Regime Mapping).
    
    Args:
        target_date: Target date in YYYY-DD-MM format
    
    Returns:
        Dict containing regime mapping results
    
    Raises:
        Pass4ExecutionError: If execution fails
    """
    logger.info(f"Pass 4: Starting regime mapping for date {target_date}")
    
    project_root = get_project_root()
    script_path = project_root / "Pass 4 - Regime Mapping" / "outputs" / "pass4_regime_mapper.py"
    
    try:
        exit_code, stdout, stderr = run_subprocess(
            script_path,
            ["--target-date", target_date],
            "Pass 4"
        )
        
        if exit_code != 0:
            error_msg = stderr or stdout or "Unknown error"
            logger.error(f"Pass 4 failed: {error_msg}")
            raise Pass4ExecutionError(f"Pass 4 execution failed with exit code {exit_code}: {error_msg}")
        
        # Load the generated output file
        output_file = project_root / "Pass 4 - Regime Mapping" / "outputs" / "factor_tilt_latest.json"
        
        if not output_file.exists():
            raise Pass4ExecutionError("Pass 4 did not generate factor_tilt_latest.json")
        
        with open(output_file, 'r') as f:
            pass4_result = json.load(f)
        
        logger.info("Pass 4: Successfully generated regime mapping")
        return pass4_result
    
    except Pass4ExecutionError:
        raise
    except Exception as e:
        logger.error(f"Pass 4: Unexpected error: {str(e)}")
        raise Pass4ExecutionError(f"Pass 4 failed: {str(e)}")


def run_pass5(target_date: str, investor_type: str) -> Dict[str, Any]:
    """
    Execute Pass 5 (Investor Allocation).
    
    Args:
        target_date: Target date in YYYY-DD-MM format
        investor_type: Investor profile type (e.g., "Conservative", "Balanced", "Aggressive")
    
    Returns:
        Dict containing portfolio scoring results
    
    Raises:
        Pass5ExecutionError: If execution fails
    """
    logger.info(f"Pass 5: Starting portfolio scoring for date {target_date}, investor {investor_type}")
    
    project_root = get_project_root()
    script_path = project_root / "Pass 5 - Portfolio Scoring" / "pass5_portfolioscorer.py"
    
    try:
        exit_code, stdout, stderr = run_subprocess(
            script_path,
            ["--target-date", target_date, "--investor-type", investor_type],
            "Pass 5"
        )
        
        if exit_code != 0:
            error_msg = stderr or stdout or "Unknown error"
            logger.error(f"Pass 5 failed: {error_msg}")
            raise Pass5ExecutionError(f"Pass 5 execution failed with exit code {exit_code}: {error_msg}")
        
        # Load the generated output file
        output_file = project_root / "Pass 5 - Portfolio Scoring" / "outputs" / "portfolio_recommendation_latest.json"
        
        if not output_file.exists():
            raise Pass5ExecutionError("Pass 5 did not generate portfolio_recommendation_latest.json")
        
        with open(output_file, 'r') as f:
            pass5_result = json.load(f)
        
        logger.info("Pass 5: Successfully generated portfolio recommendations")
        return pass5_result
    
    except Pass5ExecutionError:
        raise
    except Exception as e:
        logger.error(f"Pass 5: Unexpected error: {str(e)}")
        raise Pass5ExecutionError(f"Pass 5 failed: {str(e)}")


def run_pass6(target_date: str, investor_type: str) -> Dict[str, Any]:
    """
    Execute Pass 6 (Final Output Generation).
    
    Args:
        target_date: Target date in YYYY-DD-MM format
        investor_type: Investor profile type (e.g., "Conservative", "Balanced", "Aggressive")
    
    Returns:
        Dict containing final portfolio execution output
    
    Raises:
        Pass6ExecutionError: If execution fails
    """
    logger.info(f"Pass 6: Starting portfolio construction for date {target_date}, investor {investor_type}")
    
    project_root = get_project_root()
    script_path = project_root / "Pass 6 - Portfolio Construction" / "pass6_portfolio_constructor.py"
    
    try:
        exit_code, stdout, stderr = run_subprocess(
            script_path,
            ["--target-date", target_date, "--investor-type", investor_type],
            "Pass 6"
        )
        
        if exit_code != 0:
            error_msg = stderr or stdout or "Unknown error"
            logger.error(f"Pass 6 failed: {error_msg}")
            raise Pass6ExecutionError(f"Pass 6 execution failed with exit code {exit_code}: {error_msg}")
        
        # Load the generated output file
        output_file = project_root / "Pass 6 - Portfolio Construction" / "outputs" / "portfolio_execution_latest.json"
        
        if not output_file.exists():
            raise Pass6ExecutionError("Pass 6 did not generate portfolio_execution_latest.json")
        
        with open(output_file, 'r') as f:
            pass6_result = json.load(f)
        
        logger.info("Pass 6: Successfully generated portfolio execution")
        return pass6_result
    
    except Pass6ExecutionError:
        raise
    except Exception as e:
        logger.error(f"Pass 6: Unexpected error: {str(e)}")
        raise Pass6ExecutionError(f"Pass 6 failed: {str(e)}")
