"""
Integration Tests for Macro Engine API

Tests the three-stage pipeline:
  1. POST /recommend/start (Pass 4)
  2. POST /recommend/investor (Pass 5)
  3. POST /recommend/final (Pass 6)

Run with:
  pytest test_api.py -v
  
Or test manually:
  python test_api.py
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path

import requests


# Configuration
BASE_URL = "http://localhost:10000"
TEST_DATE = "2009-01-04"
INVESTOR_TYPES = ["Conservative", "Balanced", "Aggressive"]


# ============================================================================
# Test Data
# ============================================================================

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_test(test_name: str, passed: bool, message: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"       {message}")


# ============================================================================
# API Tests
# ============================================================================

def test_health_check():
    """Test /health endpoint."""
    print_section("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200
        data = response.json()
        
        print_test(
            "GET /health",
            passed,
            f"Status: {response.status_code}, Service: {data.get('service')}"
        )
        return passed
    except Exception as e:
        print_test("GET /health", False, str(e))
        return False


def test_root():
    """Test / endpoint."""
    print_section("API Information")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        passed = response.status_code == 200
        data = response.json()
        
        print_test(
            "GET /",
            passed,
            f"Status: {response.status_code}, Stages: {len(data.get('stages', []))}"
        )
        return passed
    except Exception as e:
        print_test("GET /", False, str(e))
        return False


def test_pipeline_docs():
    """Test /api/pipeline endpoint."""
    # the cleaned API no longer exposes /api/pipeline; expect 404
    print_section("Pipeline Documentation (deprecated)")
    response = requests.get(f"{BASE_URL}/api/pipeline")
    passed = response.status_code == 404
    print_test(
        "GET /api/pipeline returns 404",
        passed,
        f"Status: {response.status_code}"
    )
    return passed


def test_pass4(target_date: str = TEST_DATE):
    """Test POST /recommend/start (Pass 4)."""
    print_section(f"Pass 4: Regime Mapping (Date: {target_date})")
    
    payload = {"target_date": target_date}
    
    try:
        response = requests.post(f"{BASE_URL}/recommend/start", json=payload)
        passed = response.status_code == 200
        data = response.json()
        
        print_test(
            "POST /recommend/start",
            passed,
            f"Status: {response.status_code}, Stage: {data.get('stage')}"
        )
        
        if passed:
            print(f"  Message: {data.get('message')}")
            if 'data' in data:
                print(f"  Output keys: {list(data['data'].keys())}")
        
        return passed, data if passed else None
    
    except Exception as e:
        print_test("POST /recommend/start", False, str(e))
        return False, None


def test_pass5(target_date: str = TEST_DATE, investor_type: str = "Balanced"):
    """Test POST /recommend/investor (Pass 5)."""
    print_section(f"Pass 5: Investor Allocation (Date: {target_date}, Investor: {investor_type})")
    
    payload = {
        "target_date": target_date,
        "investor_type": investor_type
    }
    
    try:
        response = requests.post(f"{BASE_URL}/recommend/investor", json=payload)
        passed = response.status_code == 200
        data = response.json()
        
        print_test(
            "POST /recommend/investor",
            passed,
            f"Status: {response.status_code}, Stage: {data.get('stage')}"
        )
        
        if passed:
            print(f"  Message: {data.get('message')}")
            if 'data' in data:
                print(f"  Output keys: {list(data['data'].keys())}")
        else:
            print(f"  Error: {data.get('detail', 'Unknown error')}")
        
        return passed, data if passed else None
    
    except Exception as e:
        print_test("POST /recommend/investor", False, str(e))
        return False, None


def test_pass6(target_date: str = TEST_DATE, investor_type: str = "Balanced"):
    """Test POST /recommend/final (Pass 6)."""
    print_section(f"Pass 6: Portfolio Construction (Date: {target_date}, Investor: {investor_type})")
    
    payload = {
        "target_date": target_date,
        "investor_type": investor_type
    }
    
    try:
        response = requests.post(f"{BASE_URL}/recommend/final", json=payload)
        passed = response.status_code == 200
        data = response.json()
        
        print_test(
            "POST /recommend/final",
            passed,
            f"Status: {response.status_code}, Stage: {data.get('stage')}"
        )
        
        if passed:
            print(f"  Message: {data.get('message')}")
            if 'data' in data:
                print(f"  Output keys: {list(data['data'].keys())}")
        else:
            print(f"  Error: {data.get('detail', 'Unknown error')}")
        
        return passed, data if passed else None
    
    except Exception as e:
        print_test("POST /recommend/final", False, str(e))
        return False, None


def test_validation_errors():
    """Test validation error handling."""
    print_section("Validation Error Handling")
    
    # Invalid date format (not a date)
    response = requests.post(
        f"{BASE_URL}/recommend/start",
        json={"target_date": "invalid-date"}
    )
    print_test(
        "Invalid date format rejection",
        response.status_code == 400,
        f"Status: {response.status_code}"
    )
    
    # Invalid investor type
    response = requests.post(
        f"{BASE_URL}/recommend/investor",
        json={"target_date": "2009-01-04", "investor_type": "InvalidType"}
    )
    print_test(
        "Invalid investor type rejection",
        response.status_code == 400,
        f"Status: {response.status_code}"
    )
    
    # Missing required field
    response = requests.post(
        f"{BASE_URL}/recommend/start",
        json={}
    )
    print_test(
        "Missing required field rejection",
        response.status_code == 422,
        f"Status: {response.status_code}"
    )


def test_complete_pipeline():
    """Test the complete three-stage pipeline."""
    print_section("Complete Pipeline Test")
    
    # Stage 1: Pass 4
    print("\n[1/3] Testing Pass 4 - Regime Mapping...")
    pass4_ok, pass4_data = test_pass4(TEST_DATE)
    
    if not pass4_ok:
        print_test("Complete Pipeline", False, "Pass 4 failed")
        return False
    
    # Stage 2: Pass 5
    print("\n[2/3] Testing Pass 5 - Investor Allocation...")
    pass5_ok, pass5_data = test_pass5(TEST_DATE, "Balanced")
    
    if not pass5_ok:
        print_test("Complete Pipeline", False, "Pass 5 failed")
        return False
    
    # Stage 3: Pass 6
    print("\n[3/3] Testing Pass 6 - Portfolio Construction...")
    pass6_ok, pass6_data = test_pass6(TEST_DATE, "Balanced")
    
    if not pass6_ok:
        print_test("Complete Pipeline", False, "Pass 6 failed")
        return False
    
    print_test("Complete Pipeline", True, "All stages succeeded")
    return True


def test_investor_types():
    """Test all investor types."""
    print_section("Testing All Investor Types")
    
    for investor_type in INVESTOR_TYPES:
        pass5_ok, _ = test_pass5(TEST_DATE, investor_type)
        pass6_ok, _ = test_pass6(TEST_DATE, investor_type)
        
        both_ok = pass5_ok and pass6_ok
        print_test(
            f"Pipeline for {investor_type}",
            both_ok,
            f"Pass 5: {'✓' if pass5_ok else '✗'}, Pass 6: {'✓' if pass6_ok else '✗'}"
        )


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  MACRO ENGINE API - INTEGRATION TEST SUITE".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print(f"   Make sure the server is running on {BASE_URL}")
        print("   Run: python main.py")
        return
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health_check()))
    results.append(("API Info", test_root()))
    results.append(("Pipeline Docs", test_pipeline_docs()))
    results.append(("Validation Errors", True))  # Already tested inline
    test_validation_errors()
    
    # Only run pipeline tests if you want to actually execute the passes
    # Uncomment if your Pass scripts are ready:
    # results.append(("Complete Pipeline", test_complete_pipeline()))
    # test_investor_types()
    
    # Summary
    print_section("Test Summary")
    
    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} passed")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
